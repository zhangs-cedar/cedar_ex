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


def main():
    try:
        config = init()
        run(config)
    except Exception as e:
        print(f"运行脚本失败: {e}")
        raise Exception("运行脚本失败")

    
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

if __name__ == "__main__":
    # input_directory = input("请输入数据文件夹路径:")
    # output_name = input("请输入输出文件名:")
    # config = {
    #     "input_directory": input_directory,
    #     "output_name": output_name
    # }
    # run(config)
    main()
