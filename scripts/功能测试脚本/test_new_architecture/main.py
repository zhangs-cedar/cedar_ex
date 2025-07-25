import os
import os.path as osp
import sys
import json
import time
from typing import Dict, Any
from cedar.utils import print,create_name
import traceback

def init():
    """准备工作"""
    cedar_base_dir = os.environ.get('CEDAR_BASE_DIR',"./") 
    script_name = osp.basename(osp.dirname(__file__))
    log_dir = osp.join(cedar_base_dir, 'log', script_name)
    os.makedirs(log_dir,exist_ok=True)
    log_path = osp.join(cedar_base_dir, 'log', script_name,create_name()+".log") # 获取日志文件路径
    os.environ["LOG_PATH"] = log_path # 设置日志文件为环境变量
    print(f"日志文件保存路径: {log_path}")
    config_file_path = sys.argv[1]
    # 加载配置
    print(f"加载配置文件: {config_file_path}")
    with open(config_file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        config["log_path"] = log_path
        print(f"加载配置成功: {config}")
    return config
    
def test_error(config):
    """测试错误"""
    if config["test_error"]:
        time.sleep(2)
        print(f"测试错误")
        # 其他代码触发错误
        a = 1/0
        raise Exception("测试错误")

    
def test_tasks(config):
    """模拟任务的总步数"""
    print(f"模拟任务的总步数: {config}")
    steps = int(config["total_steps"])
    delay_seconds = float(config["delay_seconds"])
    for i in range(steps):
        time.sleep(delay_seconds)
        print(f"任务第{i+1}步")
    return True


def main():
    """主函数"""
    config = init()
    try:
        test_error(config)
        test_tasks(config)
    except Exception as e:
        # 记录详细的异常类型、消息和堆栈信息到日志文件（中文注释）
        error_type = type(e).__name__
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"测试任务失败: {error_type}: {error_msg}\n{error_trace}")
        raise
    



if __name__ == "__main__":
    main()