import sys
import os
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


if __name__ == "__main__":
    main({"name": "张三"})