import os
import os.path as osp
import sys
import json
import time
from cedar.utils import print, create_name, try_except


def init(config_file_path):
    """准备工作"""
    if config_file_path is None:
        config_file_path = os.environ.get('SCRIPT_CONFIG_FILE')
        print(f'从环境变量获取配置文件路径: {config_file_path}')
        if config_file_path is None and len(sys.argv) > 1:
            config_file_path = sys.argv[1]
        if config_file_path is None:
            raise ValueError('未提供配置文件路径')
    else:
        print(f'从命令行参数获取配置文件路径: {config_file_path}')
    cedar_base_dir = os.environ.get('CEDAR_BASE_DIR', './')
    script_name = osp.basename(osp.dirname(__file__))
    log_dir = osp.join(cedar_base_dir, 'log', script_name)
    os.makedirs(log_dir, exist_ok=True)
    log_path = osp.join(cedar_base_dir, 'log', script_name, create_name() + '.log')  # 获取日志文件路径
    os.environ['LOG_PATH'] = log_path  # 设置日志文件为环境变量
    print(f'日志文件保存路径: {log_path}')
    # 加载配置
    print(f'加载配置文件: {config_file_path}')
    with open(config_file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        print(f'加载配置成功: {config}')
    return config


def test_error(config):
    """测试错误"""
    if config['test_error']:
        time.sleep(2)
        print(f'测试错误')
        # 其他代码触发错误
        a = 1 / 0
        raise Exception('测试错误')


def test_tasks(config):
    """模拟任务的总步数"""
    print(f'模拟任务的总步数: {config}')
    steps = int(config['total_steps'])
    delay_seconds = float(config['delay_seconds'])
    for i in range(steps):
        time.sleep(delay_seconds)
        print(f'任务第{i + 1}步')
    return True


@try_except  # 装饰器，捕获异常并记录到日志文件
def main(config_file_path=None):
    """主函数

    Args:
        config_file_path: 配置文件路径，如果为None则从环境变量或命令行参数获取
    """
    config = init(config_file_path)
    test_tasks(config)
    test_error(config)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
