import os
import json
import subprocess
import tempfile
import threading
import time
import queue
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from datetime import datetime
from cedar.utils import print


def get_script_file_path(script_dir):
    """获取脚本文件的路径"""
    main_py = os.path.join(script_dir, 'main.py')
    if os.path.exists(main_py):
        return main_py

    for file in os.listdir(script_dir):
        if (file.startswith('main.cpython-') or file.startswith('main.cp')) and (
            file.endswith('.so') or file.endswith('.pyd')
        ):
            return os.path.join(script_dir, file)

    return None


class ScriptExecutor(QObject):
    """脚本执行器 - 负责脚本的安全执行和日志监控"""

    # 信号定义
    log_received = pyqtSignal(str)  # 接收到新日志
    script_started = pyqtSignal(str)  # 脚本开始执行
    script_finished = pyqtSignal(int)  # 脚本执行完成，返回退出码
    script_error = pyqtSignal(str)  # 脚本执行错误
    stop_timer_signal = pyqtSignal()  # 用于主线程安全stop QTimer

    def __init__(self, scripts_dir: str):
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
        """运行脚本"""
        try:
            # 停止之前的脚本
            self.stop_script()

            # 创建临时日志文件
            self.log_file_path = tempfile.mktemp(suffix='.log')
            self.current_script_name = script_rel_path

            # 准备脚本执行
            script_dir = os.path.abspath(os.path.join(self.scripts_dir, script_rel_path))
            script_path = get_script_file_path(script_dir)

            if not script_path:
                self.script_error.emit(f'脚本文件不存在: {script_dir}')
                return False

            # 创建临时配置文件
            config_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
            json.dump(config, config_file, ensure_ascii=False, indent=2)
            config_file.close()

            # 设置环境变量
            env = os.environ.copy()
            env['SCRIPT_LOG_FILE'] = self.log_file_path
            if cedar_base_dir is not None:
                env['CEDAR_BASE_DIR'] = os.path.abspath(cedar_base_dir)

            # 启动脚本进程
            if script_path.endswith(('.so', '.pyd')):
                # 对于编译后的文件，使用 Python 模块导入方式执行
                script_dir_escaped = os.path.abspath(script_dir).replace('\\', '\\\\')
                config_file_escaped = os.path.abspath(config_file.name).replace('\\', '\\\\')

                cmd = [
                    'python',
                    '-c',
                    f"""
import sys
import os
os.chdir('{script_dir_escaped}')
sys.path.insert(0, '{script_dir_escaped}')

try:
    import main
    if hasattr(main, 'main'):
        os.environ['SCRIPT_CONFIG_FILE'] = '{config_file_escaped}'
        try:
            main.main('{config_file_escaped}')
        except TypeError:
            main.main()
    else:
        print("脚本模块已加载，但未找到main函数")
except Exception as e:
    print(f"执行编译脚本时出错: {{e}}")
    sys.exit(1)
""",
                ]
            else:
                # 对于 .py 文件，直接执行
                cmd = ['python', script_path, config_file.name]

            print(f'启动脚本: {" ".join(cmd)}')
            self.current_process = subprocess.Popen(cmd, text=True, bufsize=1, env=env)

            # 启动监控
            self.is_running = True
            self.last_log_position = 0
            self.monitor_timer.start(500)

            # 启动进程监控线程
            monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
            monitor_thread.start()

            self.script_started.emit(script_rel_path)
            return True

        except Exception as e:
            print(f'启动脚本失败: {e}')
            self.script_error.emit(f'启动脚本失败: {str(e)}')
            return False

    def stop_script(self):
        """停止当前运行的脚本"""
        if self.monitor_timer:
            self.stop_timer_signal.emit()

        self.is_running = False

        if self.current_process:
            try:
                self.current_process.terminate()

                try:
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print('脚本未在5秒内终止，强制结束')
                    self.current_process.kill()
                    self.current_process.wait()

            except Exception as e:
                print(f'停止脚本时出错: {e}')
            finally:
                self.current_process = None

    def _monitor_process(self):
        """监控脚本进程状态"""
        if not self.current_process:
            return

        try:
            exit_code = self.current_process.wait()
            self._append_script_log_to_main_log()
            self.script_finished.emit(exit_code)

        except Exception as e:
            print(f'监控进程时出错: {e}')
            self.script_error.emit(f'监控进程时出错: {str(e)}')
        finally:
            self.is_running = False
            if self.monitor_timer:
                self.stop_timer_signal.emit()

    def _monitor_log_file(self):
        """监控日志文件变化"""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return

        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_log_position)
                new_content = f.read()
                if new_content:
                    self.last_log_position = f.tell()
                    lines = new_content.splitlines()
                    for line in lines:
                        if line.strip():
                            self.log_received.emit(line.strip())

        except Exception as e:
            print(f'读取日志文件时出错: {e}')

    def _append_script_log_to_main_log(self):
        """将本次运行的脚本日志内容追加到 /log/app.log"""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return

        try:
            main_log_path = os.path.join(os.getcwd(), 'log', 'app.log')
            with open(self.log_file_path, 'r', encoding='utf-8') as src, open(
                main_log_path, 'a', encoding='utf-8'
            ) as dst:
                dst.write('\n' + '=' * 60 + '\n')
                dst.write(
                    f'脚本运行日志 [{self.current_script_name}] @ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                )
                dst.write('-' * 60 + '\n')
                for line in src:
                    dst.write(line)
                dst.write('\n' + '=' * 60 + '\n')
        except Exception as e:
            print(f'追加脚本日志到主日志失败: {e}')

    def cleanup(self):
        """清理资源"""
        self.stop_script()

        if self.log_file_path and os.path.exists(self.log_file_path):
            try:
                os.remove(self.log_file_path)
            except Exception as e:
                print(f'删除临时日志文件失败: {e}')

        self.log_file_path = None

    def _stop_monitor_timer(self):
        if self.monitor_timer:
            self.monitor_timer.stop()
