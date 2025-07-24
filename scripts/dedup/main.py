import os
import hashlib
from typing import Dict, Set

def calc_md5(file_path: str) -> str:
    """计算文件的MD5值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def main(config: dict):
    """
    文件去重（根据MD5和文件名）
    Args:
        config: 配置字典，包含 'target_dir'（目标目录）、'mode'（去重模式：md5/name/both）、'delete'（是否删除重复文件）
    """
    target_dir = config.get("target_dir", "")
    mode = config.get("mode", "both")
    delete = config.get("delete", False)
    if not target_dir or not os.path.isdir(target_dir):
        print("请指定有效的目标目录")
        return
    seen: Set[str] = set()
    name_seen: Set[str] = set()
    md5_seen: Set[str] = set()
    dup_files = []
    for root, _, files in os.walk(target_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            key = None
            if mode == "md5":
                md5 = calc_md5(fpath)
                key = md5
            elif mode == "name":
                key = fname
            else:  # both
                md5 = calc_md5(fpath)
                key = f"{fname}_{md5}"
            if key in seen:
                dup_files.append(fpath)
            else:
                seen.add(key)
    if dup_files:
        print(f"发现重复文件 {len(dup_files)} 个：")
        for f in dup_files:
            print(f)
        if delete:
            for f in dup_files:
                try:
                    os.remove(f)
                    print(f"已删除: {f}")
                except Exception as e:
                    print(f"删除失败: {f}, 错误: {e}")
    else:
        print("未发现重复文件。") 