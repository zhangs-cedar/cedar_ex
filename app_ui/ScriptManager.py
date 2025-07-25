import os
import importlib.util
import subprocess
from typing import List, Dict, Any

class ScriptManager:
    """脚本管理器，负责脚本的发现、加载和执行"""
    def __init__(self, scripts_dir: str):
        """
        初始化脚本管理器
        Args:
            scripts_dir: 脚本目录路径
        """
        self.scripts_dir = scripts_dir
        self.scripts = self.discover_scripts()

    def discover_scripts(self) -> List[str]:
        """
        发现所有可用脚本
        Returns:
            脚本名称列表
        """
        scripts = []
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir)
        for entry in os.listdir(self.scripts_dir):
            subdir = os.path.join(self.scripts_dir, entry)
            if os.path.isdir(subdir) and os.path.exists(os.path.join(subdir, "main.py")):
                scripts.append(entry)
        return scripts

    def run_script(self, script_name: str, config: Dict[str, Any]) -> subprocess.Popen:
        """
        以子进程方式运行脚本，返回Popen对象，主程序可捕获其stdout/stderr。
        Args:
            script_name: 脚本名称
            config: 配置参数字典
        Returns:
            Popen对象
        """
        import json
        # 打印参数日志（中文注释）
        script_dir = os.path.join(self.scripts_dir, script_name)
        script_path = os.path.join(script_dir, "main.py")
        # 将config写入临时json
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as tf:
            json.dump(config, tf, ensure_ascii=False)
            tf.flush()
            config_path = tf.name
        # 用python执行main.py，传入config路径
        cmd = ["python", script_path, config_path]
        print(f"[脚本执行参数] cmd: {cmd}")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        return proc 