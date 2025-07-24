import sys
import os
try:
    import json5
except ImportError:
    raise ImportError("请先安装json5库: pip install json5")
from loguru import logger
import yaml

def main(config: dict) -> None:
    """
    打印问候信息
    Args:
        config: 配置字典，包含 'name'
    """
    name = config.get("name", "世界")
    print(f"你好, {name}！")
    # 打印配置
    logger.info(f"配置: {config}")

def load_config_from_yaml(yaml_path: str) -> dict:
    """
    从YAML文件加载配置，提取fields为config字典
    Args:
        yaml_path: YAML配置文件路径
    Returns:
        配置字典
    """
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"配置文件不存在: {yaml_path}")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    config = {}
    for field in data.get('fields', []):
        config[field['name']] = field.get('default')
    return config

if __name__ == "__main__":
    # 支持命令行参数指定yaml路径
    if len(sys.argv) > 1:
        yaml_path = sys.argv[1]
        config = load_config_from_yaml(yaml_path)
        main(config)
    elif os.path.exists("form.yaml"):
        config = load_config_from_yaml("form.yaml")
        main(config)
    else:
        main({"name": "张三"})