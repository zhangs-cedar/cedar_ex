import os
import json
import subprocess
import tempfile
import threading
import time
import queue
from typing import Dict, Any, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from datetime import datetime
from cedar.utils import print

class ScriptExecutor(QObject):
    """脚本执行器 - 负责脚本的安全执行和日志监控"""
    
    # 信号定义
    log_received = pyqtSignal(str)  # 接收到新日志
    script_started = pyqtSignal(str)  # 脚本开始执行
    script_finished = pyqtSignal(int)  # 脚本执行完成，返回退出码
    script_error = pyqtSignal(str)  # 脚本执行错误
    stop_timer_signal = pyqtSignal()  # 用于主线程安全stop QTimer
    
    def __init__(self, scripts_dir: str):
        """
        初始化脚本执行器
        
        Args:
            scripts_dir: 脚本目录路径
        """
        super().__init__()
        self.scripts_dir = scripts_dir
        self.current_process: Optional[subprocess.Popen] = None
        self.log_file_path: Optional[str] = None
        self.monitor_timer: Optional[QTimer] = None
        self.log_queue = queue.Queue()
        self.is_running = False
        self.last_log_position = 0
        self.current_script_name: Optional[str] = None
        
        # 创建监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._monitor_log_file)
        self.stop_timer_signal.connect(self._stop_monitor_timer)
        
    def run_script(self, script_rel_path: str, config: Dict[str, Any], cedar_base_dir: str = None) -> bool:
        """
        运行脚本
        
        Args:
            script_rel_path: 脚本相对路径
            config: 配置参数
            cedar_base_dir: CEDAR工程根目录
        Returns:
            是否成功启动脚本
        """
        try:
            # 停止之前的脚本
            self.stop_script()
            # 创建临时日志文件
            self.log_file_path = tempfile.mktemp(suffix='.log')
            self.current_script_name = script_rel_path
            # 准备脚本执行
            script_dir = os.path.join(self.scripts_dir, script_rel_path)
            script_path = os.path.join(script_dir, "main.py")
            if not os.path.exists(script_path):
                self.script_error.emit(f"脚本文件不存在: {script_path}")
                return False
            # 创建临时配置文件
            config_file = tempfile.NamedTemporaryFile(
                mode="w", 
                delete=False, 
                suffix=".json", 
                encoding="utf-8"
            )
            json.dump(config, config_file, ensure_ascii=False, indent=2)
            config_file.close()
            # 设置环境变量，让脚本知道日志文件路径
            env = os.environ.copy()
            env['SCRIPT_LOG_FILE'] = self.log_file_path
            if cedar_base_dir is not None:
                env['CEDAR_BASE_DIR'] = cedar_base_dir
            # 启动脚本进程
            cmd = ["python", script_path, config_file.name]
            print(f"启动脚本: {' '.join(cmd)}")
            self.current_process = subprocess.Popen(
                cmd,
                # stdout=None,  # 让输出继承父进程
                # stderr=None,  # 让输出继承父进程
                text=True,
                bufsize=1,
                env=env
            )
            # 启动监控线程
            self.is_running = True
            self.last_log_position = 0
            # 启动日志监控定时器（每500ms检查一次）
            self.monitor_timer.start(500)
            # 启动进程监控线程
            monitor_thread = threading.Thread(
                target=self._monitor_process, 
                daemon=True
            )
            monitor_thread.start()
            self.script_started.emit(script_rel_path)
            return True
        except Exception as e:
            print(f"启动脚本失败: {e}")
            self.script_error.emit(f"启动脚本失败: {str(e)}")
            return False
    
    def stop_script(self) -> None:
        """停止当前运行的脚本"""
        if self.monitor_timer:
            self.stop_timer_signal.emit()
        
        self.is_running = False
        
        if self.current_process:
            try:
                # 尝试优雅终止
                self.current_process.terminate()
                
                # 等待5秒，如果还没结束则强制终止
                try:
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("脚本未在5秒内终止，强制结束")
                    self.current_process.kill()
                    self.current_process.wait()
                    
            except Exception as e:
                print(f"停止脚本时出错: {e}")
            finally:
                self.current_process = None
    
    def _monitor_process(self) -> None:
        """监控脚本进程状态"""
        if not self.current_process:
            return
            
        try:
            # 等待进程结束
            exit_code = self.current_process.wait()
            
            # 追加本次运行日志到 /log/app.log
            self._append_script_log_to_main_log()
            
            # 在主线程中发送完成信号
            self.script_finished.emit(exit_code)
            
        except Exception as e:
            print(f"监控进程时出错: {e}")
            self.script_error.emit(f"监控进程时出错: {str(e)}")
        finally:
            self.is_running = False
            if self.monitor_timer:
                self.stop_timer_signal.emit()
    
    def _monitor_log_file(self) -> None:
        """监控日志文件变化"""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return
            
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                # 移动到上次读取的位置
                f.seek(self.last_log_position)
                
                # 读取新内容
                new_content = f.read()
                if new_content:
                    # 更新位置
                    self.last_log_position = f.tell()
                    
                    # 按行分割并发送日志信号
                    lines = new_content.splitlines()
                    for line in lines:
                        if line.strip():
                            self.log_received.emit(line.strip())
                            
        except Exception as e:
            print(f"读取日志文件时出错: {e}")
    
    def _append_script_log_to_main_log(self) -> None:
        """将本次运行的脚本日志内容追加到 /log/app.log"""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return
        try:
            main_log_path = os.path.join(os.getcwd(), "log", "app.log")
            with open(self.log_file_path, 'r', encoding='utf-8') as src, \
                 open(main_log_path, 'a', encoding='utf-8') as dst:
                dst.write("\n" + "="*60 + "\n")
                dst.write(f"脚本运行日志 [{self.current_script_name}] @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                dst.write("-"*60 + "\n")
                for line in src:
                    dst.write(line)
                dst.write("\n" + "="*60 + "\n")
        except Exception as e:
            print(f"追加脚本日志到主日志失败: {e}")
    
    def cleanup(self) -> None:
        """清理资源"""
        self.stop_script()
        
        # 删除临时日志文件
        if self.log_file_path and os.path.exists(self.log_file_path):
            try:
                os.remove(self.log_file_path)
            except Exception as e:
                print(f"删除临时日志文件失败: {e}")
        
        self.log_file_path = None 

    def _stop_monitor_timer(self):
        if self.monitor_timer:
            self.monitor_timer.stop() 