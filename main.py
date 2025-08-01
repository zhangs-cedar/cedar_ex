import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QTextEdit,
    QLabel,
    QMessageBox,
    QFormLayout,
    QGroupBox,
    QScrollArea,
    QFrame,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QDateEdit,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from app_ui.ScriptExecutor import ScriptExecutor
from app_ui.FormBuilder import FormBuilder

from typing import Dict, Any
from cedar.utils import print

# ==================== 配置参数 ====================
WINDOW_TITLE = '脚本执行器'
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 1200
FONT_SIZE = 12
FONT_FAMILY = 'Microsoft YaHei'
LOG_MONITOR_INTERVAL = 200

# 路径配置
CEDAR_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath('scripts')
CONFIGS_DIR = os.path.abspath('configs')
LOG_FILE = os.path.abspath('log/app.log')
os.environ['LOG_PATH'] = LOG_FILE


def get_tree_item_path(item):
    """获取树节点完整路径"""
    path_parts = []
    while item:
        path_parts.insert(0, item.text(0))
        item = item.parent()
    return path_parts


def has_script_file(script_dir):
    """检查脚本目录中是否有可执行的脚本文件"""
    if not os.path.isdir(script_dir):
        return False

    main_py = os.path.join(script_dir, 'main.py')
    if os.path.exists(main_py):
        return True

    for file in os.listdir(script_dir):
        if (file.startswith('main.cpython-') or file.startswith('main.cp')) and (
            file.endswith('.so') or file.endswith('.pyd')
        ):
            return True

    return False


def should_skip_directory(dir_name):
    """判断是否应该跳过某个目录"""
    skip_patterns = ['.build', '__pycache__', '.git', '.svn', '.hg', 'node_modules', '.vscode', '.idea']

    if dir_name in skip_patterns or dir_name.endswith('.build'):
        return True
    return False


def has_valid_subdirs(dir_path):
    """检查目录是否有有效的子目录"""
    try:
        for entry in os.listdir(dir_path):
            entry_path = os.path.join(dir_path, entry)
            if os.path.isdir(entry_path) and not should_skip_directory(entry):
                return True
    except (OSError, PermissionError):
        pass
    return False


class ScriptExecutorUI(QMainWindow):
    """脚本执行器主窗口"""

    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # 设置窗口图标
        icon_path = os.path.join(CEDAR_BASE_DIR, 'app_ui', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.set_global_font()

        self.script_executor = ScriptExecutor(SCRIPTS_DIR)
        self.form_builder = FormBuilder(self)
        self.script_executor.log_received.connect(self.append_log)
        self.script_executor.script_started.connect(self.on_script_started)
        self.script_executor.script_finished.connect(self.on_script_finished)
        self.script_executor.script_error.connect(self.on_script_error)

        self.init_ui()
        self.load_scripts()

        self.log_signal.connect(self.append_log)
        self.log_file_offsets: Dict[str, int] = {}
        self.log_monitor_timer = QTimer(self)
        self.log_monitor_timer.timeout.connect(self.monitor_log_dir)
        self.init_log_offsets()
        self.log_monitor_timer.start(LOG_MONITOR_INTERVAL)

    def set_global_font(self):
        font = QFont()
        font.setPointSize(FONT_SIZE)
        if FONT_FAMILY:
            font.setFamily(FONT_FAMILY)
        QApplication.setFont(font)

    def append_log(self, msg: str):
        self.log_text.append(msg)
        QTimer.singleShot(0, self._scroll_log_to_end)

    def _scroll_log_to_end(self):
        self.log_text.moveCursor(self.log_text.textCursor().End)
        self.log_text.ensureCursorVisible()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        main_splitter = QSplitter(Qt.Vertical)
        h_splitter = QSplitter(Qt.Horizontal)

        # 左侧：脚本树
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)
        script_title = QLabel('可用脚本')
        script_title.setStyleSheet('margin-bottom: 8px;')
        left_panel.addWidget(script_title)

        self.script_tree = QTreeWidget()
        self.script_tree.setHeaderHidden(True)
        self.script_tree.setMinimumWidth(400)
        self.script_tree.setMaximumWidth(600)
        self.script_tree.itemSelectionChanged.connect(self.on_script_selected)
        left_panel.addWidget(self.script_tree)

        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        h_splitter.addWidget(left_widget)

        # 右侧：配置参数
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)
        param_group = QGroupBox('配置参数')
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
        self.run_btn = QPushButton('运行脚本')
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
        log_panel = QVBoxLayout()
        log_frame = QFrame()
        log_frame.setFrameShape(QFrame.HLine)
        log_frame.setFrameShadow(QFrame.Sunken)
        log_panel.addWidget(log_frame)

        log_group = QGroupBox('日志输出')
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

    def init_log_offsets(self):
        """初始化日志文件偏移量"""
        log_dir = os.path.abspath('log')
        if not os.path.exists(log_dir):
            print('[提示] 日志目录不存在')
            self.append_log('[提示] 日志目录不存在')
            return

        for root, _, files in os.walk(log_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'rb') as f:
                        f.seek(0, 2)
                        self.log_file_offsets[fpath] = f.tell()
                except Exception:
                    self.log_file_offsets[fpath] = 0

    def load_scripts(self):
        """加载脚本树"""
        self.script_tree.clear()
        if not os.path.exists(SCRIPTS_DIR):
            QMessageBox.critical(self, '错误', f'脚本目录不存在: {SCRIPTS_DIR}')
            return

        def add_items(parent_item, dir_path):
            for entry in sorted(os.listdir(dir_path)):
                if should_skip_directory(entry):
                    continue

                full_path = os.path.join(dir_path, entry)
                if os.path.isdir(full_path):
                    has_script = has_script_file(full_path)
                    has_subdir = has_valid_subdirs(full_path)
                    if has_script or has_subdir:
                        item = QTreeWidgetItem([entry])
                        parent_item.addChild(item)
                        add_items(item, full_path)

        for entry in sorted(os.listdir(SCRIPTS_DIR)):
            if should_skip_directory(entry):
                continue

            full_path = os.path.join(SCRIPTS_DIR, entry)
            if os.path.isdir(full_path):
                has_script = has_script_file(full_path)
                has_subdir = has_valid_subdirs(full_path)
                if has_script or has_subdir:
                    item = QTreeWidgetItem([entry])
                    self.script_tree.addTopLevelItem(item)
                    add_items(item, full_path)

        self.script_tree.expandAll()

    def on_script_selected(self):
        """脚本选择事件"""
        selected_items = self.script_tree.selectedItems()
        if not selected_items:
            self.clear_form()
            self.run_btn.hide()
            return

        item = selected_items[0]
        path_parts = get_tree_item_path(item)
        if not path_parts:
            self.clear_form()
            self.run_btn.hide()
            return

        script_name = path_parts[-1]
        script_dir = os.path.abspath(os.path.join(SCRIPTS_DIR, *path_parts))

        if not has_script_file(script_dir):
            self.clear_form()
            self.run_btn.hide()
            return

        # 显示文档
        doc_path = os.path.abspath(os.path.join(script_dir, 'README.md'))
        if os.path.exists(doc_path):
            with open(doc_path, 'r', encoding='utf-8') as f:
                doc_content = f.read().strip()
            if doc_content:
                self.doc_label.setText(doc_content)
                self.doc_label.show()
            else:
                self.doc_label.hide()
        else:
            self.doc_label.hide()

        # 显示配置文件路径
        config_path = os.path.abspath(os.path.join(CONFIGS_DIR, f'{script_name}.json'))
        if os.path.exists(config_path):
            self.config_label.setText(f'配置文件: {config_path}')
            self.config_label.show()
        else:
            self.config_label.hide()

        # 构建表单
        self.clear_form()
        yaml_path = os.path.abspath(os.path.join(script_dir, 'form.yaml'))
        if os.path.exists(yaml_path):
            self.form_fields = self.form_builder.build_form(self.form_layout, yaml_path)
        else:
            self.form_fields = {}

        self.run_btn.show()

    def clear_form(self):
        """清空表单"""
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.form_fields = {}

    def get_widget_value(self, widget):
        """获取控件值"""
        widget_value_getters = {
            QCheckBox: lambda w: w.isChecked(),
            QListWidget: lambda w: [item.text() for item in w.selectedItems()],
            QSpinBox: lambda w: w.value(),
            QDoubleSpinBox: lambda w: w.value(),
            QComboBox: lambda w: w.currentText(),
            QDateEdit: lambda w: w.date().toString('yyyy-MM-dd'),
        }

        for widget_type, getter in widget_value_getters.items():
            if isinstance(widget, widget_type):
                return getter(widget)

        if hasattr(widget, 'currentText') and callable(widget.currentText):
            return widget.currentText()
        if hasattr(widget, 'text') and callable(widget.text):
            return widget.text()
        if hasattr(widget, 'value') and callable(widget.value):
            return widget.value()
        if hasattr(widget, 'date') and callable(widget.date):
            return widget.date().toString('yyyy-MM-dd')
        return None

    def run_script(self):
        """运行脚本"""
        item = self.script_tree.currentItem()
        if not item:
            QMessageBox.warning(self, '提示', '请先选择一个脚本')
            return

        path_parts = get_tree_item_path(item)
        if not path_parts:
            QMessageBox.warning(self, '提示', '请先选择一个脚本')
            return

        script_rel_path = os.path.join(*path_parts)
        config_path = os.path.abspath(os.path.join(CONFIGS_DIR, f'{path_parts[-1]}.json'))

        # 获取配置
        config = {}
        if hasattr(self, 'form_fields') and self.form_fields:
            for k, w in self.form_fields.items():
                try:
                    config[k] = self.get_widget_value(w)
                except Exception:
                    config[k] = None
        elif os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

        success = self.script_executor.run_script(script_rel_path, config, CEDAR_BASE_DIR)
        if not success:
            QMessageBox.critical(self, '错误', '启动脚本失败')

    def on_script_started(self, script_name: str):
        """脚本开始执行"""
        print(f'脚本开始执行: {script_name}')
        self.append_log(f'脚本开始执行: {script_name}')
        self.run_btn.setEnabled(False)
        self.form_widget.setEnabled(False)
        self.run_btn.setText('运行中...')

    def on_script_finished(self, exit_code: int):
        """脚本执行完成"""
        if exit_code == 0:
            print('脚本执行完成')
            self.append_log('脚本执行完成')
        else:
            print(f'脚本执行失败，退出码: {exit_code}')
            self.append_log(f'脚本执行失败，退出码: {exit_code}')
        self.run_btn.setEnabled(True)
        self.form_widget.setEnabled(True)
        self.run_btn.setText('运行脚本')

    def on_script_error(self, error_msg: str):
        """脚本执行错误"""
        print(f'脚本执行错误: {error_msg}')
        self.append_log(f'脚本执行错误: {error_msg}')
        QMessageBox.critical(self, '错误', f'脚本执行错误: {error_msg}')
        self.run_btn.setEnabled(True)
        self.form_widget.setEnabled(True)
        self.run_btn.setText('运行脚本')

    def closeEvent(self, event):
        """窗口关闭事件"""
        if hasattr(self, 'script_executor'):
            self.script_executor.cleanup()
        if hasattr(self, 'log_monitor_timer'):
            self.log_monitor_timer.stop()
        event.accept()

    def monitor_log_dir(self):
        """监控日志目录"""
        log_dir = os.path.abspath('log')
        if not os.path.exists(log_dir):
            print('[提示] 日志目录不存在')
            self.append_log('[提示] 日志目录不存在')
            return

        for root, _, files in os.walk(log_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    last_offset = self.log_file_offsets.get(fpath, 0)
                    with open(fpath, 'r', encoding='utf-8') as f:
                        f.seek(last_offset)
                        new_content = f.read()
                        if new_content:
                            rel_path = os.path.relpath(fpath, log_dir)
                            for line in new_content.splitlines():
                                if line.strip():
                                    self.append_log(f'[{rel_path}] {line.strip()}')
                            self.log_file_offsets[fpath] = f.tell()
                except Exception as e:
                    print(f'[日志监控异常] {fname}: {e}')
                    self.append_log(f'[日志监控异常] {fname}: {e}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ScriptExecutorUI()
    win.show()
    sys.exit(app.exec_())
