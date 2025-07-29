import yaml
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QWidget,
    QDateEdit,
    QFileDialog,
    QFormLayout,
)
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QListWidget, QListWidgetItem


class FormBuilder:
    """表单生成器，根据 YAML 配置动态生成表单控件"""

    def __init__(self, parent=None):
        self.parent = parent

    def build_form(self, form_layout: QFormLayout, yaml_path: str) -> Dict[str, Any]:
        """根据 YAML 配置生成表单控件"""
        form_fields = {}
        with open(yaml_path, 'r', encoding='utf-8') as f:
            form_cfg = yaml.safe_load(f)

        for field in form_cfg.get('fields', []):
            name = field['name']
            label = field.get('label', name)
            ftype = field.get('type', 'text')
            default = field.get('default', '')
            widget = None

            if ftype == 'text':
                widget = QLineEdit()
                widget.setText(str(default))
            elif ftype == 'multiline':
                widget = QTextEdit()
                widget.setPlainText(str(default))
            elif ftype == 'int':
                widget = QSpinBox()
                widget.setValue(int(default) if default != '' else 0)
                widget.setMinimum(field.get('min', -2147483648))
                widget.setMaximum(field.get('max', 2147483647))
            elif ftype == 'float':
                widget = QDoubleSpinBox()
                widget.setValue(float(default) if default != '' else 0.0)
                widget.setMinimum(field.get('min', -1e10))
                widget.setMaximum(field.get('max', 1e10))
                widget.setDecimals(field.get('decimals', 2))
            elif ftype == 'bool':
                widget = QCheckBox()
                widget.setChecked(bool(default))
            elif ftype == 'select' and field.get('multiple', False):
                widget = QListWidget()
                widget.setSelectionMode(QListWidget.MultiSelection)
                options = field.get('options', [])
                for opt in options:
                    item = QListWidgetItem(str(opt))
                    widget.addItem(item)
                    if isinstance(default, list) and opt in default:
                        item.setSelected(True)
                    elif isinstance(default, str) and opt == default:
                        item.setSelected(True)
                widget.setMinimumHeight(min(200, 32 + 24 * len(options)))
                form_layout.addRow(label, widget)
                form_fields[name] = widget
                continue
            elif ftype == 'select':
                widget = QComboBox()
                for opt in field.get('options', []):
                    widget.addItem(str(opt))
                if default:
                    idx = widget.findText(str(default))
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
            elif ftype == 'file':
                widget = QLineEdit()
                widget.setText(str(default))
                btn = QPushButton('选择文件')
                widget.setMinimumHeight(28)
                btn.setMinimumHeight(28)

                def choose_file(w):
                    path, _ = QFileDialog.getOpenFileName(self.parent, '选择文件')
                    if path:
                        w.setText(path)

                btn.clicked.connect(lambda _, w=widget: choose_file(w))
                file_layout = QHBoxLayout()
                file_layout.setContentsMargins(0, 0, 0, 0)
                file_layout.setSpacing(6)
                file_layout.addWidget(widget)
                file_layout.addWidget(btn)
                file_widget = QWidget()
                file_widget.setLayout(file_layout)
                form_layout.addRow(label, file_widget)
                form_fields[name] = widget
                continue
            elif ftype == 'dir':
                widget = QLineEdit()
                widget.setText(str(default))
                btn = QPushButton('选择目录')
                widget.setMinimumHeight(28)
                btn.setMinimumHeight(28)

                def choose_dir(w):
                    path = QFileDialog.getExistingDirectory(self.parent, '选择目录')
                    if path:
                        w.setText(path)

                btn.clicked.connect(lambda _, w=widget: choose_dir(w))
                dir_layout = QHBoxLayout()
                dir_layout.setContentsMargins(0, 0, 0, 0)
                dir_layout.setSpacing(6)
                dir_layout.addWidget(widget)
                dir_layout.addWidget(btn)
                dir_widget = QWidget()
                dir_widget.setLayout(dir_layout)
                form_layout.addRow(label, dir_widget)
                form_fields[name] = widget
                continue
            elif ftype == 'date':
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                if default:
                    try:
                        y, m, d = map(int, str(default).split('-'))
                        widget.setDate(QDate(y, m, d))
                    except Exception:
                        widget.setDate(QDate.currentDate())
                else:
                    widget.setDate(QDate.currentDate())
            elif ftype == 'doc':
                doc_content = field.get('content', '')
                doc_widget = QTextEdit()
                doc_widget.setReadOnly(True)
                doc_widget.setPlainText(str(doc_content))
                doc_widget.setMinimumHeight(60)
                form_layout.addRow(label, doc_widget)
                continue

            if widget:
                form_layout.addRow(label, widget)
                form_fields[name] = widget

        return form_fields
