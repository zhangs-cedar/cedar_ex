# CedarEx 脚本执行平台

## 项目简介

CedarEx 是一个基于 PyQt6 的桌面应用，面向自动化脚本的统一管理、配置和执行。用户可通过可视化界面，便捷地选择、配置和运行各类 Python 脚本，并实时查看日志输出，适用于数据分析、批处理等多种场景。

---

## 快速开始

### 运行方式
   进入项目根目录，执行：
   ```shell
   python main.py
   ```
## 环境配置
- 推荐使用项目内置的env环境，避免依赖冲突
**注意**：建议将conda环境创建在项目目录下，且命名为`env`，这样项目可以自动识别并使用该环境。
### 1. 创建conda环境
在项目根目录下创建最小Python环境：
```shell
# 创建名为env的conda环境（Python 3.8）
conda create -p ./env python=3.8 -y

# 激活虚拟环境然后安装cedar包
pip install tools/cedar-1.0.1-py3-none-any.whl

# 验证cedar包安装
python -c "import cedar; print('cedar包安装成功')"
# 安装requirements.txt
pip install -r requirements.txt
```




## 使用流程

```yaml
开始
 ↓
启动 CedarEx 主程序
 ↓
左侧选择需要执行的脚本
 ↓
中间区域自动加载脚本参数表单（支持YAML配置）
 ↓
填写参数，点击“运行脚本”
 ↓
实时查看下方日志输出
 ↓
脚本执行完成后，可在/log目录查看详细日志
```

---

## 主要功能

- **脚本管理**：自动发现 `scripts/` 目录下的所有脚本（需包含 main.py | form.yaml）。
- **参数配置**：支持通过 YAML 文件动态生成参数表单，灵活配置脚本参数。
- **日志管理**：执行日志实时显示，并自动归档到 `log/` 目录。
- **多脚本支持**：可同时管理和切换多个脚本项目。

---

## 目录结构说明

```yaml
main.py                # 主程序入口
start.bat / start.vbs  # 一键启动脚本
app_ui/                # 前端界面与核心逻辑
scripts/               # 用户自定义脚本目录（每个子目录为一个脚本项目）
log/                   # 日志输出目录
env/                   # 内置Python环境（建议conda环境创建在项目目录下，且命名为env）
tools/                 # 工具脚本目录
```

---

## 常见问题

- **Q: 如何添加新脚本？**  
  A: 在 `scripts/` 下新建文件夹，放入 `main.py`，并按需添加参数配置文件（如 config.yaml）。

- **Q: 日志在哪里查看？**  
  A: 实时日志在主界面下方，历史日志在 `log/` 目录。

---

如需详细开发或二次集成，请参考 `app_ui/` 目录下各模块源码。 