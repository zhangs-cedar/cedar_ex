#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 Nuitka 打包脚本
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

def run_cmd(cmd, check=True, show_output=False):
    """运行命令"""
    print(f"执行: {' '.join(cmd)}")
    start_time = time.time()
    

    # 实时显示输出
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                text=True, bufsize=1, universal_newlines=True)
    
    for line in process.stdout:
        print(f"  {line.rstrip()}")
    
    process.wait()
    result = subprocess.CompletedProcess(cmd, process.returncode, "", "")

    
    elapsed_time = time.time() - start_time
    print(f"  完成 (耗时: {elapsed_time:.1f}秒)")
    
    if result.returncode != 0 and check:
        print(f"错误: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    
    return result

def count_python_files(directory):
    """统计目录中的 Python 文件数量"""
    count = 0
    for path in Path(directory).rglob("*.py"):
        if path.name != "__init__.py":
            count += 1
    return count

def main():
    # 配置
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist" / "main.dist"
    conda_env = "/opt/homebrew/anaconda3/envs/py310"
    python_exe = f"{conda_env}/bin/python"
    
    print("=" * 60)
    print("Cedar Ex 轻量化打包工具")
    print("=" * 60)
    
    # 统计文件数量
    app_ui_files = count_python_files(project_root / "app_ui")
    scripts_files = count_python_files(project_root / "scripts")
    total_files = app_ui_files + scripts_files + 1  # +1 for main.py
    
    print(f"项目根目录: {project_root}")
    print(f"输出目录: {dist_dir}")
    print(f"Conda 环境: {conda_env}")
    print(f"需要编译的文件: {total_files} 个")
    print(f"  - app_ui: {app_ui_files} 个")
    print(f"  - scripts: {scripts_files} 个")
    print(f"  - main.py: 1 个")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # 清理目录
        print("步骤 1/7: 清理打包目录...")
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        dist_dir.mkdir(parents=True)
        print("  ✓ 清理完成")
        
        # 安装 Nuitka
        # print("步骤 2/7: 检查 Nuitka...")
        # run_cmd([python_exe, "-m", "pip", "install", "nuitka"])
        
        # 构建 app_ui 模块
        print(f"步骤 2/7: 构建 app_ui 模块 ({app_ui_files} 个文件)...")
        app_ui_dir = dist_dir / "app_ui"
        app_ui_dir.mkdir()
        
        current_file = 0
        for py_file in (project_root / "app_ui").glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            current_file += 1
            print(f"  [{current_file}/{app_ui_files}] 构建: {py_file.name}")
            run_cmd([
                python_exe, "-m", "nuitka",
                "--module",
                f"--output-dir={app_ui_dir}",
                str(py_file)
            ], show_output=False)
        
        # 构建 scripts 模块
        print(f"步骤 3/7: 构建 scripts 模块 ({scripts_files} 个文件)...")
        scripts_dir = dist_dir / "scripts"
        
        def build_scripts_recursive(src_path, dst_path, current_count):
            dst_path.mkdir(parents=True, exist_ok=True)
            
            for item in src_path.iterdir():
                if item.is_file() and item.suffix == ".py":
                    if item.name == "__init__.py":
                        continue
                    current_count[0] += 1
                    print(f"  [{current_count[0]}/{scripts_files}] 构建脚本: {item.relative_to(project_root / 'scripts')}")
                    run_cmd([
                        python_exe, "-m", "nuitka",
                        "--module",
                        f"--output-dir={dst_path}",
                        str(item)
                    ], show_output=False)
                elif item.is_dir():
                    build_scripts_recursive(item, dst_path / item.name, current_count)
                elif item.is_file():
                    shutil.copy2(item, dst_path / item.name)
        
        current_count = [0]
        build_scripts_recursive(project_root / "scripts", scripts_dir, current_count)
        
        # 构建主程序
        print("步骤 4/7: 构建主程序...")
        run_cmd([
            python_exe, "-m", "nuitka",
            "--module",
            "--include-data-dir=log=log",
            f"--output-dir={dist_dir}",
            str(project_root / "main.py")
        ], show_output=False)
        
        # 复制虚拟环境
        print("步骤 5/7: 复制虚拟环境...")
        venv_dir = dist_dir / "my_venv"
        shutil.copytree(conda_env, venv_dir)
        print("  ✓ 虚拟环境复制完成")
        
        # 清理虚拟环境
        print("步骤 6/7: 清理虚拟环境...")
        cleaned_files = 0
        for pattern in ["__pycache__", "*.pyc", "*.pyo"]:
            for path in venv_dir.rglob(pattern):
                if path.is_dir():
                    shutil.rmtree(path)
                    cleaned_files += 1
                else:
                    path.unlink()
                    cleaned_files += 1
        print(f"  ✓ 清理了 {cleaned_files} 个缓存文件")
        
        # 复制额外文件
        print("步骤 7/7: 复制额外文件...")
        for extra_dir in ["configs", "log"]:
            src = project_root / extra_dir
            if src.exists():
                shutil.copytree(src, dist_dir / extra_dir)
                print(f"  ✓ 复制 {extra_dir} 目录")
        
        # 创建启动脚本
        run_script = dist_dir / "run.sh"
        with open(run_script, "w") as f:
            f.write("""#!/bin/bash
# 设置 Python 环境
export PYTHONPATH="$PWD/app_ui:$PWD/scripts:$PYTHONPATH"
# 使用虚拟环境中的 Python 运行主程序
$PWD/my_venv/bin/python -c "
import sys
import os
sys.path.insert(0, '$PWD')
import main
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
from main import ScriptExecutorUI
win = ScriptExecutorUI()
win.show()
sys.exit(app.exec_())
"
""")
        os.chmod(run_script, 0o755)
        print("  ✓ 创建启动脚本")
        
        total_time = time.time() - start_time
        
        print("=" * 60)
        print("🎉 打包完成！")
        print("=" * 60)
        print(f"输出目录: {dist_dir}")
        print(f"总耗时: {total_time:.1f} 秒")
        print(f"平均每个文件: {total_time/total_files:.1f} 秒")
        print("\n运行方式:")
        print(f"  cd {dist_dir}")
        print("  ./run.sh")
        print("=" * 60)
        
    except Exception as e:
        total_time = time.time() - start_time
        print(f"\n❌ 打包失败 (耗时: {total_time:.1f} 秒)")
        print(f"错误信息: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 