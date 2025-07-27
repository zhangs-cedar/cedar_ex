#!/bin/bash
# 设置 Python 环境
export PYTHONPATH="$PWD/app_ui:$PWD/scripts:$PYTHONPATH"
# 使用虚拟环境中的 Python 运行主程序
$PWD/my_venv/bin/python -c "
import sys
import os
sys.path.insert(0, '$PWD')
# 导入并运行编译后的主程序
import main
# 创建 QApplication 并启动 GUI
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
from main import ScriptExecutorUI
win = ScriptExecutorUI()
win.show()
sys.exit(app.exec_())
" 