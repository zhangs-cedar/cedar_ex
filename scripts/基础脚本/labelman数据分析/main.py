import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import os.path as osp
import pandas as pd
from typing import Dict, Any
from utils import DataProcessor, DefectChart
import yaml
from loguru import logger



def main(config: Dict[str, Any]) -> None:
    """
    只实现生成html功能：处理输入目录下所有json，生成html图表
    """
    input_directory = config.get("input_directory", "")
    output_name = config.get("output_name", "result")
    html_filename = osp.join(input_directory, f"{output_name}.html")

    logger.info(f"开始处理目录: {input_directory}")
    processor = DataProcessor(input_directory)
    processor.process_directory()
    df = pd.DataFrame(processor.df_data)
    if df.empty:
        logger.error("未获取到有效数据，无法生成html")
        return
    chart = DefectChart(df)
    scatter_chart = chart.create_scatter_chart()
    bar_chart = chart.create_bar_chart(chart.value_counts)
    (scatter_chart | bar_chart).save(html_filename, inline=True)
    logger.info(f"图表已保存至: {html_filename}")


if __name__ == "__main__":
    input_directory = input("请输入输入目录：")
    output_name = input("请输入保存文件名：")
    config = {
        "input_directory": input_directory,
        "output_name": output_name
    }
    main(config)
