import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QTextEdit, QLabel, QMessageBox,
    QFormLayout, QGroupBox, QScrollArea, QFrame, QTreeWidget, QTreeWidgetItem,
    QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from app_ui.ScriptManager import ScriptManager
from app_ui.FormBuilder import FormBuilder
from app_ui.LoggerManager import LoggerManager
from loguru import logger
from typing import Dict, Any

SCRIPTS_DIR = "scripts"
CONFIGS_DIR = "configs"
LOG_FILE = "log/app.log"

class ScriptExecutor(QMainWindow):
    """脚本执行器主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("脚本执行器")
        self.resize(1200, 800)
        
        # 设置全局字体，与窗口标题保持一致
        self.set_global_font()
        
        self.script_manager = ScriptManager(SCRIPTS_DIR)
        self.logger_manager = LoggerManager(LOG_FILE, self.append_log)
        self.form_builder = FormBuilder(self)
        self.init_ui()
        self.load_scripts()
        # 移除自定义QSS样式，保持PyQt默认风格
        # self.setStyleSheet(...)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)
        # 主体和日志区用垂直QSplitter分割
        main_splitter = QSplitter(Qt.Vertical)
        # 主区左右用水平QSplitter分割
        h_splitter = QSplitter(Qt.Horizontal)
        # 左侧：脚本树卡片
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)
        script_title = QLabel("可用脚本")
        script_title.setStyleSheet("margin-bottom: 8px;")
        left_panel.addWidget(script_title)
        self.script_tree = QTreeWidget()
        self.script_tree.setHeaderHidden(True)
        self.script_tree.setMinimumWidth(250)
        self.script_tree.setMaximumWidth(350)
        self.script_tree.itemSelectionChanged.connect(self.on_script_selected)
        left_panel.addWidget(self.script_tree)
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        h_splitter.addWidget(left_widget)
        # 右侧：仅配置参数卡片
        from PyQt5.QtWidgets import QGroupBox, QScrollArea
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)
        param_group = QGroupBox("配置参数")
        param_layout = QVBoxLayout()
        self.doc_label = QLabel()
        self.doc_label.setWordWrap(True)
        self.doc_label.hide()
        param_layout.addWidget(self.doc_label)
        self.config_label = QLabel()
        self.config_label.hide()
        param_layout.addWidget(self.config_label)
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.form_layout.setHorizontalSpacing(18)
        self.form_layout.setVerticalSpacing(8)
        self.form_widget = QWidget()
        self.form_widget.setLayout(self.form_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.form_widget)
        param_layout.addWidget(scroll)
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("运行脚本")
        self.run_btn.clicked.connect(self.run_script)
        self.run_btn.hide()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addStretch(1)
        param_layout.addLayout(btn_layout)
        param_group.setLayout(param_layout)
        right_panel.addWidget(param_group)
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        h_splitter.addWidget(right_widget)
        h_splitter.setSizes([300, 900])
        main_splitter.addWidget(h_splitter)
        # 日志区
        from PyQt5.QtWidgets import QFrame
        log_panel = QVBoxLayout()
        log_frame = QFrame()
        log_frame.setFrameShape(QFrame.HLine)
        log_frame.setFrameShadow(QFrame.Sunken)
        log_panel.addWidget(log_frame)
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        log_panel.addWidget(log_group)
        log_widget = QWidget()
        log_widget.setLayout(log_panel)
        main_splitter.addWidget(log_widget)
        main_splitter.setSizes([700, 200])
        main_layout.addWidget(main_splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def set_global_font(self) -> None:
        """设置全局字体，与窗口标题保持一致"""
        # 获取系统默认字体
        font = QFont()
        # 设置字体大小为12pt（与窗口标题大小相近）
        font.setPointSize(12)
        # 应用到整个应用
        QApplication.setFont(font)

    def append_log(self, msg: str) -> None:
        self.log_text.append(msg)

    def load_scripts(self) -> None:
        self.script_tree.clear()
        def add_items(parent_item, dir_path):
            for entry in sorted(os.listdir(dir_path)):
                full_path = os.path.join(dir_path, entry)
                if os.path.isdir(full_path):
                    has_main = os.path.exists(os.path.join(full_path, "main.py"))
                    has_subdir = any(os.path.isdir(os.path.join(full_path, e)) for e in os.listdir(full_path))
                    if has_main or has_subdir:
                        item = QTreeWidgetItem([entry])
                        parent_item.addChild(item)
                        add_items(item, full_path)
        # 直接以 scripts/ 下的一级目录为顶层节点
        for entry in sorted(os.listdir(SCRIPTS_DIR)):
            full_path = os.path.join(SCRIPTS_DIR, entry)
            if os.path.isdir(full_path):
                has_main = os.path.exists(os.path.join(full_path, "main.py"))
                has_subdir = any(os.path.isdir(os.path.join(full_path, e)) for e in os.listdir(full_path))
                if has_main or has_subdir:
                    item = QTreeWidgetItem([entry])
                    self.script_tree.addTopLevelItem(item)
                    add_items(item, full_path)
        self.script_tree.expandAll()

    def on_script_selected(self):
        selected_items = self.script_tree.selectedItems()
        if not selected_items:
            self.config_label.setText("配置文件: 无")
            self.doc_label.hide()
            self.clear_form()
            self.run_btn.hide()
            return
        item = selected_items[0]
        # 递归获取完整路径
        path_parts = []
        node = item
        while node:
            path_parts.insert(0, node.text(0))
            node = node.parent()
        if not path_parts:
            self.config_label.hide()
            self.doc_label.hide()
            self.clear_form()
            self.run_btn.hide()
            return
        script_name = path_parts[-1]
        script_dir = os.path.join(SCRIPTS_DIR, *path_parts)
        # 只允许叶子节点（含 main.py 的目录）可选
        if not os.path.exists(os.path.join(script_dir, "main.py")):
            self.config_label.hide()
            self.doc_label.hide()
            self.clear_form()
            self.run_btn.hide()
            return
        config_path = os.path.join(CONFIGS_DIR, f"{script_name}.json")
        yaml_path = os.path.join(script_dir, "form.yaml")
        doc_path = os.path.join(script_dir, "README.md")
        # 说明文档合并到配置参数卡片顶部
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                doc_content = f.read().strip()
            if doc_content:
                self.doc_label.setText(doc_content)
                self.doc_label.show()
            else:
                self.doc_label.hide()
        else:
            self.doc_label.hide()
        if os.path.exists(config_path):
            self.config_label.setText(f"配置文件: {config_path}")
            self.config_label.show()
        else:
            self.config_label.hide()
        self.clear_form()
        if os.path.exists(yaml_path):
            self.form_fields = self.form_builder.build_form(self.form_layout, yaml_path)
        else:
            self.form_fields = {}
        self.run_btn.show()

    def clear_form(self) -> None:
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.form_fields = {}

    def run_script(self) -> None:
        item = self.script_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个脚本")
            return
        # 递归获取完整路径
        path_parts = []
        node = item
        while node:
            path_parts.insert(0, node.text(0))
            node = node.parent()
        if not path_parts:
            QMessageBox.warning(self, "提示", "请先选择一个脚本")
            return
        script_rel_path = os.path.join(*path_parts)  # 传递完整相对路径
        script_dir = os.path.join(SCRIPTS_DIR, script_rel_path)
        config_path = os.path.join(CONFIGS_DIR, f"{path_parts[-1]}.json")
        config = {}
        if hasattr(self, "form_fields") and self.form_fields:
            for k, w in self.form_fields.items():
                # 只处理常见控件类型，FormBuilder 已保证类型
                try:
                    config[k] = w.text() if hasattr(w, 'text') else w.value() if hasattr(w, 'value') else w.currentText() if hasattr(w, 'currentText') else w.isChecked() if hasattr(w, 'isChecked') else w.date().toString("yyyy-MM-dd") if hasattr(w, 'date') else None
                except Exception:
                    config[k] = None
        elif os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        logger = self.logger_manager.get_logger()
        logger.info(f"开始执行脚本: {script_rel_path}")
        self.script_manager.run_script(script_rel_path, config)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ScriptExecutor()
    win.show()
    sys.exit(app.exec_()) 