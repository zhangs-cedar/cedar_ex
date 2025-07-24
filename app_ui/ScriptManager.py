import os
import importlib.util
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

    def run_script(self, script_name: str, config: Dict[str, Any]) -> None:
        """
        加载并执行指定脚本
        Args:
            script_name: 脚本名称
            config: 配置参数字典
        """
        script_dir = os.path.join(self.scripts_dir, script_name)
        script_path = os.path.join(script_dir, "main.py")
        try:
            spec = importlib.util.spec_from_file_location("user_script", script_path)
            user_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(user_script)
            if hasattr(user_script, "main"):
                user_script.main(config)
            else:
                print("脚本未定义 main(config) 函数")
        except Exception as e:
            print(f"脚本执行出错: {e}") 