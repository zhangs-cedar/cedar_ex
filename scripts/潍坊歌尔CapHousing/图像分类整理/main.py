import os
import os.path as osp
import sys
import json
from PIL import Image
from tqdm import tqdm
from cedar.image import is_image
from cedar.utils import print, create_name, try_except, get_files_list, copy_file, find_duplicate_filenames


def parse_filepath(filepath: str) -> dict:
    """解析文件路径获取点位信息"""
    filename = os.path.splitext(os.path.basename(filepath))[0]
    sp_name = filename.split('_')
    # 获取文件信息
    fileinfo = dict()
    fileinfo['dianwei'] = sp_name[0].split('-')[0] + '_' + sp_name[1]
    return fileinfo


def get_image_size(file_path: str):
    """获取图像尺寸"""
    with Image.open(file_path) as img:
        width, height = img.size
    return width, height


def process_images(config: dict) -> bool:
    """处理图像文件，进行分类整理"""
    input_dir = config['input_dir']
    save_dir = config['save_dir']
    keep_original_tree = config.get('keep_original_tree', False)
    keep_jpg = config.get('keep_jpg', False)
    copy_json = config.get('copy_json', True)

    # 获取支持的文件格式
    supported_suffixes = ['.png']
    if keep_jpg:
        supported_suffixes.append('.jpg')

    # 获取文件列表
    files = get_files_list(input_dir)
    print(f'找到 {len(files)} 个文件')

    processed_count = 0
    error_count = 0

    for file in files:
        if not is_image(file['path']):
            continue
        if file['suffix'] not in supported_suffixes:
            continue
        try:
            # 解析文件路径获取点位信息
            fileinfo = parse_filepath(file['path'])
            print(f'处理文件: {os.path.basename(file["path"])} -> 点位: {fileinfo["dianwei"]}')

            # 获取图像尺寸
            width, height = get_image_size(file['path'])

            # 构建保存路径
            pipeline_name = fileinfo['dianwei']
            date_str = file['modification_time'].strftime('%Y-%m-%d')
            size_str = f'{width}_{height}'

            if keep_original_tree:
                # 计算相对于 input_dir 的路径，保持完整的目录结构
                relative_path = os.path.relpath(file['path'], input_dir)
                relative_dir = os.path.dirname(relative_path)
                if relative_dir:  # 如果有子目录
                    _save_dir = osp.join(
                        save_dir, pipeline_name, f'{date_str}_{pipeline_name}_{size_str}', relative_dir
                    )
                else:  # 如果文件直接在 input_dir 下
                    _save_dir = osp.join(save_dir, pipeline_name, f'{date_str}_{pipeline_name}_{size_str}')
            else:
                _save_dir = osp.join(save_dir, pipeline_name, f'{date_str}_{pipeline_name}_{size_str}')

            # 复制图像文件
            copy_file(file['path'], _save_dir)
            processed_count += 1

            # 复制对应的JSON文件
            if copy_json:
                try:
                    json_path = file['path'].replace(file['suffix'], '.json')
                    if os.path.exists(json_path):
                        copy_file(json_path, _save_dir)
                        print(f'复制JSON文件: {os.path.basename(json_path)}')
                except Exception as e:
                    print(f'复制JSON文件失败: {e}')

        except Exception as e:
            print(f'处理文件失败 {file["path"]}: {e}')
            error_count += 1
            continue

    print(f'处理完成: 成功 {processed_count} 个文件, 失败 {error_count} 个文件')
    duplicates = find_duplicate_filenames(input_dir)

    if len(duplicates) > 0:
        print('以下文件名重复：')
    for duplicate in duplicates:
        print(duplicate)

    if len(duplicates) == 0:
        print('没有发现重复文件')
        exit()
    return error_count == 0


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


@try_except
def main(config_file_path: str = None) -> bool:
    config = init(config_file_path)
    process_images(config)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
