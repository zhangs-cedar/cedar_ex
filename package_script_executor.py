#!/usr/bin/env python3
"""
简化版脚本执行器打包程序
仅用于将 main.py 打包为独立的 exe 文件
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


def check_nuitka() -> bool:
    """检查 Nuitka 是否安装"""
    print("=== 检查打包依赖 ===")
    try:
        result = subprocess.run(
            ["python", "-m", "nuitka", "--version"],
            capture_output=True, text=True, check=True
        )
        version_line = result.stdout.strip().split('\n')[0]
        print(f"✅ Nuitka 版本: {version_line}")
        return True
    except Exception:
        print("❌ 错误: 未安装 Nuitka\n请运行: pip install nuitka")
        return False


def clean_output_dir(output_dir: Path) -> None:
    """清理输出目录"""
    if output_dir.exists():
        print(f"清理输出目录: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(exist_ok=True)
    print(f"创建输出目录: {output_dir}")


def build_exe(product_name: str, output_dir: Path, nuitka_options: List[str]) -> bool:
    """使用 Nuitka 构建 exe 文件，并实时显示进度和日志"""
    print("\n=== 构建可执行文件 ===")
    cmd = [
        "python", "-m", "nuitka"
    ] + nuitka_options + [
        f"--output-dir={output_dir}",
        f"--output-filename={product_name}.exe",
        "main.py"
    ]
    print(f"执行命令: {' '.join(str(x) for x in cmd)}")
    import shlex
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        # 实时输出
        for line in process.stdout:
            print(line, end='')
        process.wait()
        if process.returncode == 0:
            print("✅ 构建成功")
            exe_path = output_dir / f"{product_name}.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"可执行文件: {exe_path} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"❌ 构建失败，退出码: {process.returncode}")
            return False
    except Exception as e:
        print(f"❌ 构建失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="简化版脚本执行器打包程序")
    parser.add_argument(
        '--output-dir', '-o',
        default='dist',
        help="输出目录"
    )
    parser.add_argument(
        '--product-name', '-p',
        default='ScriptExecutor',
        help="产品名称"
    )
    parser.add_argument(
        '--version', '-v',
        default='1.0.0',
        help="版本号"
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    product_name = args.product_name
    # Nuitka 常用参数，可根据需要调整
    nuitka_options = [
        "--standalone",
        "--onefile",
        "--windows-console-mode=disable",
        "--include-package=app_ui",
        "--include-package=loguru",
        "--include-package=PyQt5",
        "--include-data-dir=scripts=scripts",
        "--include-data-dir=configs=configs",
        "--assume-yes-for-downloads",
        "--show-progress",
        "--show-memory",
        "--enable-plugin=pyqt5",
        "--windows-icon-from-ico=app_ui/icon.ico"
    ]

    if not check_nuitka():
        sys.exit(1)
    if not Path("main.py").exists():
        print("❌ 错误: 未找到 main.py 文件")
        sys.exit(1)
    clean_output_dir(output_dir)
    success = build_exe(product_name, output_dir, nuitka_options)
    if success:
        print("\n✅ 打包成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 打包失败！")
        sys.exit(1)


if __name__ == "__main__":
    main() 