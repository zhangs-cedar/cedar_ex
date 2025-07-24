from loguru import logger
from typing import Dict, Any

def main(config: Dict[str, Any]) -> None:
    """测试表单各类型控件的功能
    Args:
        config: 配置参数字典
    """
    logger.info("--- 表单控件测试 ---")
    logger.info(f"目录选择: {config.get('test_dir', '')}")
    logger.info(f"文件选择: {config.get('test_file', '')}")
    logger.info(f"布尔判断: {config.get('is_active', False)}")
    logger.info(f"单选选择: {config.get('color', '')}")
    logger.info(f"多选选择: {config.get('hobbies', [])}")
    hobbies = config.get('hobbies', [])
    if isinstance(hobbies, str):
        hobbies = [h.strip() for h in hobbies.split(',') if h.strip()]
    logger.info(f"多选解析后: {hobbies}")
    logger.info("--- END ---")