import os
import os.path as osp
import sys
import json
import time
import numpy as np
import cv2
from cedar.image import imread, imwrite
from cedar.draw import putText,color_list
from cedar.utils import print, create_name, try_except,rmtree_makedirs


def init(config_file_path):
    """初始化配置和日志
    """
    if config_file_path is None:
        config_file_path = os.environ.get('SCRIPT_CONFIG_FILE')
        print(f"从环境变量获取配置文件路径: {config_file_path}")
        if config_file_path is None and len(sys.argv) > 1:
            config_file_path = sys.argv[1]
        if config_file_path is None:
            raise ValueError("未提供配置文件路径")
    else:
        print(f"从命令行参数获取配置文件路径: {config_file_path}")
    
    cedar_base_dir = os.environ.get('CEDAR_BASE_DIR', "./")
    script_name = osp.basename(osp.dirname(__file__))
    log_dir = osp.join(cedar_base_dir, 'log', script_name)
    os.makedirs(log_dir, exist_ok=True)
    log_path = osp.join(cedar_base_dir, 'log', script_name, create_name() + ".log")
    os.environ["LOG_PATH"] = log_path
    print(f"日志文件保存路径: {log_path}")
    
    # 加载配置
    print(f"加载配置文件: {config_file_path}")
    with open(config_file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        print(f"加载配置成功: {config}")
    return config


def stack_images_with_fixed_num_per_row(imgs: list, num_per_row: int) -> np.ndarray:
    """将 NumPy 矩阵形式的图像列表拼接成一个大图像
    
    Args:
        imgs: 图像列表（每个图像为一个 NumPy 矩阵）
        num_per_row: 每行的图像数量
        
    Returns:
        拼接后的图像
    """
    # 检查所有图像的大小是否一致
    img_height, img_width = imgs[0].shape[:2]
    for img in imgs:
        if img.shape[:2] != (img_height, img_width):
            raise ValueError("所有图像的大小必须一致！")

    # 计算总行数
    num_rows = (len(imgs) + num_per_row - 1) // num_per_row

    # 创建一个空白画布
    canvas_width = img_width * num_per_row
    canvas_height = img_height * num_rows
    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    # 将图像逐行拼接到画布上
    for i, img in enumerate(imgs):
        row = i // num_per_row
        col = i % num_per_row
        x_offset = col * img_width
        y_offset = row * img_height
        canvas[y_offset:y_offset + img_height, x_offset:x_offset + img_width] = img

    return canvas


def parse_b698_filepath_mp(filepath: str) -> dict:
    """解析B698文件路径信息
    
    Args:
        filepath: 文件路径
        
    Returns:
        文件信息字典
    """
    filename = os.path.splitext(os.path.basename(filepath))[0]
    sp_name = filename.split("_")

    # get fileinfo
    fileinfo = dict()
    fileinfo["type"] = sp_name[0]
    fileinfo["id"] = sp_name[4]
    fileinfo["position"] = sp_name[1]
    fileinfo["timestamp"] = sp_name[9]
    fileinfo["index"] = sp_name[3]

    return fileinfo


def compare_images(input_dir: str, save_dir: str, config: dict) -> bool:
    """比较图像一致性
    
    Args:
        input_dir: 输入目录
        save_dir: 保存目录
        config: 配置字典
        
    Returns:
        是否成功
    """
    print(f"开始图像一致性比较")
    print(f"输入目录: {input_dir}")
    print(f"保存目录: {save_dir}")
    
    all_images = {}
    camera_key_list = []
    _camera_key_list = os.listdir(input_dir)
    
    for _camera in _camera_key_list:
        __camera_key_list = os.listdir(osp.join(input_dir, _camera))
        for __camera in __camera_key_list:
            camera_key_list.append(_camera + "/" + __camera)
    
    print(f"发现相机目录: {camera_key_list}")

    # 收集所有图像
    for camera in camera_key_list:
        img_dic = {}
        idx_key_list = []
        for root, dirs, files in os.walk(osp.join(input_dir, camera)):
            for file in files:
                try:
                    file_path = osp.join(root, file)
                    names = osp.basename(file_path)
                    name, suffix = osp.splitext(names)
                    key = parse_b698_filepath_mp(file_path)["index"]
                    idx_key_list.append(key)
                    if suffix not in [".jpg", ".png", ".bmp"]:
                        continue
                    img_dic[key] = file_path
                except Exception as e:
                    print(f"名字解析问题: {file_path}, 错误: {e}")
        all_images[camera] = img_dic
    
    print(f"索引列表: {idx_key_list}")
    print(f"相机列表: {camera_key_list}")
    
    # 生成对比图像
    for idx in idx_key_list:
        imgs = []
        for category in all_images.keys():
            try:
                if category not in all_images.keys():
                    print(f"category:{category} not in all_images")
                if idx not in all_images[category].keys():
                    print(f"idx:{idx} not in {category}")
                print(f"category:{category},idx:{idx}")
                file_path = all_images[category][idx]
                img = imread(file_path)
                img = putText(img, "xj:" + category, (10, 10), text_color=tuple(color_list[2]), text_size=config.get("text_size", 80))
                img = putText(img, "idx:" + str(idx), (10, 200), text_color=tuple(color_list[2]), text_size=config.get("index_text_size", 120))
                downsample_level = config.get("downsample_level", 2)
                for _ in range(downsample_level):
                    img = cv2.pyrDown(img)
                imgs.append(img)
            except Exception as e:
                print(f"处理图像时出错: {e}")

        if imgs:
            imgs = stack_images_with_fixed_num_per_row(imgs, num_per_row=config.get("num_per_row", 10))
            os.makedirs(save_dir, exist_ok=True)
            imwrite(osp.join(save_dir, f"{idx}.png"), imgs)
    
    print(f"图像一致性比较完成，结果保存到: {save_dir}")
    return True


@try_except
def main(config_file_path: str = None) -> None:
    """主函数
    
    Args:
        config_file_path: 配置文件路径，如果为None则从环境变量或命令行参数获取
    """
    config = init(config_file_path)
    
    # 获取输入和输出目录
    input_dir = config.get("input_dir")
    save_dir = config.get("save_dir")
    # 清理输出目录
    if config.get("clean_output", True):
        rmtree_makedirs(save_dir)
    
    # 执行图像比较
    compare_images(input_dir, save_dir, config)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None) 