import os
import os.path as osp
import json
import time
import pandas as pd
from typing import Dict, Any
from cedar.utils import print,create_name,try_except

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import DataProcessor, DefectChart



def init(config_file_path):
    """准备工作"""
    if config_file_path is None:
        config_file_path = os.environ.get('SCRIPT_CONFIG_FILE')
        print(f"从环境变量获取配置文件路径: {config_file_path}")
        if config_file_path is None and len(sys.argv) > 1:
            config_file_path = sys.argv[1]
        if config_file_path is None:
            raise ValueError("未提供配置文件路径")
    else:
        print(f"从命令行参数获取配置文件路径: {config_file_path}")
    cedar_base_dir = os.environ.get('CEDAR_BASE_DIR',"./") 
    script_name = osp.basename(osp.dirname(__file__))
    log_dir = osp.join(cedar_base_dir, 'log', script_name)
    os.makedirs(log_dir,exist_ok=True)
    log_path = osp.join(cedar_base_dir, 'log', script_name,create_name()+".log") # 获取日志文件路径
    os.environ["LOG_PATH"] = log_path # 设置日志文件为环境变量
    print(f"日志文件保存路径: {log_path}")
    # 加载配置
    print(f"加载配置文件: {config_file_path}")
    with open(config_file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        print(f"加载配置成功: {config}")
    return config




    
def run(config):
    print("开始运行脚本")
    input_directory = config.get("input_directory", "")
    output_name = config.get("output_name", "result")
    html_filename = osp.join(input_directory, f"{output_name}.html")
    print(f"开始处理目录: {input_directory}")
    processor = DataProcessor(input_directory)
    processor.process_directory()
    df = pd.DataFrame(processor.df_data)
    if df.empty:
        print("未获取到有效数据，无法生成html")
        return
    chart = DefectChart(df)
    scatter_chart = chart.create_scatter_chart()
    bar_chart = chart.create_bar_chart(chart.value_counts)
    (scatter_chart | bar_chart).save(html_filename, inline=True)
    print(f"图表已保存至: {html_filename}")


@try_except # 装饰器，捕获异常并记录到日志文件
def main(config_file_path=None):
    """主函数
    
    Args:
        config_file_path: 配置文件路径，如果为None则从环境变量或命令行参数获取
    """
    config = init(config_file_path)
    run(config)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
