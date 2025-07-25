import os
import os.path as osp
import sys
import json
import time
from typing import Dict, Any
from cedar.utils import print,create_name


def load_config(config_file_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}


def main(config_file_path: str):
    """主函数"""

    cedar_base_dir = os.environ.get('CEDAR_BASE_DIR')
    script_name = osp.basename(osp.dirname(__file__))
    log_dir = osp.join(cedar_base_dir, 'log', script_name)
    print(f"log_dir: {log_dir}")
    os.makedirs(log_dir,exist_ok=True)
    log_file_path = osp.join(cedar_base_dir, 'log', script_name,create_name()+".log") # 获取日志文件路径
    print(f"log_file_path: {log_file_path}",file=log_file_path)

    # 打印日志
    print(f"CEDAR_BASE_DIR: {cedar_base_dir}",file=log_file_path)
    print(f"开始执行脚本",file=log_file_path) 
    config_file_path = sys.argv[1]
    # 加载配置
    print(f"加载配置文件: {config_file_path}",file=log_file_path)
    time.sleep(5)
    print(f"等待5秒",file=log_file_path)
    config = load_config(config_file_path)
    print(f"加载配置: {config}",file=log_file_path)
    
    



if __name__ == "__main__":
    main("")