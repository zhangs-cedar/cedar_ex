import os
import os.path as osp
import json
import time
import pandas as pd
from typing import Dict, Any
from cedar.utils import print,create_name

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import DataProcessor, DefectChart




def init():
    """准备工作"""
    cedar_base_dir = os.environ.get('CEDAR_BASE_DIR')
    script_name = osp.basename(osp.dirname(__file__))
    log_dir = osp.join(cedar_base_dir, 'log', script_name)
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = osp.join(log_dir, f"{int(time.time())}.log")
    print(f"log_file_path: {log_file_path}",file=log_file_path)

def main(config_file_path: str):
    """
    主函数，处理输入目录下所有json，生成html图表
    Args:
        config_file_path: 配置文件路径
    """
    cedar_base_dir = os.environ.get('CEDAR_BASE_DIR')
    script_name = osp.basename(osp.dirname(__file__))
    log_dir = osp.join(cedar_base_dir, 'log', script_name)
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = osp.join(log_dir, f"{int(time.time())}.log")



    print(f"CEDAR_BASE_DIR: {cedar_base_dir}")
    print(f"开始执行脚本: {script_name}")
    print(f"加载配置文件: {config_file_path}")

    config = load_config(config_file_path)
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python main.py <config_file_path>")
        sys.exit(1)
    main(sys.argv[1])
