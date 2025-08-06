# CedarEx 轻量化打包指南

## 🎯 概述

CedarEx 轻量化打包工具是一个专为 Windows 环境设计的 Python 应用程序打包解决方案。该工具采用创新的轻量化策略，将 Python 代码编译为二进制文件，同时保持依赖库的动态加载能力。

### 主要特性
- ✅ **轻量化打包**：只编译代码，不打包依赖
- ✅ **动态依赖加载**：从虚拟环境动态加载所有依赖库
- ✅ **最小化体积**：主程序只包含编译后的代码逻辑
- ✅ **跨平台兼容**：专为 Windows 环境优化
- ✅ **一键部署**：自动生成启动脚本和压缩包

## 🚀 打包策略

### 核心思想
- **代码编译**：所有 Python 代码使用 Nuitka 编译为二进制文件
- **依赖分离**：所有依赖库从 `my_venv/` 目录动态加载
- **体积优化**：主程序只包含编译后的代码逻辑，大幅减少打包体积

### 技术架构
```
源代码 → Nuitka编译 → 二进制模块 → 轻量化打包
    ↓
虚拟环境 → 依赖库 → 动态加载 → 运行时环境
```

## 💻 系统要求

### 必需环境
- **操作系统**: Windows 10/11
- **Python**: 3.8+ (推荐使用 Conda 环境)
- **编译器**: Nuitka
- **GUI框架**: PyQt6

## 📦 使用方法

### 1. 基本打包
```bash
# 运行打包工具
python tools/pa_win.py
```

### 2. 高级打包选项
```bash
# 只打包源码，不复制虚拟环境
python tools/pa_win.py --no-venv

# 不创建压缩包
python tools/pa_win.py --no-compress

# 组合使用
python tools/pa_win.py --no-venv --no-compress
```

### 3. 运行打包后的程序
```bash
# 方式1: 使用批处理文件 (有控制台窗口)
cd dist/main.dist
run.bat

# 方式2: 使用VBS脚本 (无控制台窗口)
cd dist/main.dist
run.vbs

```

## 📁 打包结果

### 目录结构
```
dist/main.dist/
├── main.py               # 编译后的主程序模块
├── app_ui/               # 编译后的GUI模块
│   ├── FormBuilder.py
│   ├── ScriptExecutor.py
│   └── icon.ico
├── scripts/              # 编译后的脚本模块
├── my_venv/              # 完整的虚拟环境
│   ├── python.exe
│   ├── Lib/
│   └── Scripts/
├── configs/              # 配置文件目录
├── log/                  # 日志目录
├── run.bat               # Windows启动脚本
└── run.vbs               # 无窗口启动脚本
```

### 文件说明
- **编译文件**: 所有 `.py` 文件被编译为 `.pyd` 或 `.exe` 文件
- **虚拟环境**: 包含完整的 Python 解释器和所有依赖库
- **启动脚本**: 自动配置环境变量和 Python 路径
- **配置文件**: 保持原有的配置和日志结构

## ⚙️ 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--no-venv` | 不复制虚拟环境，只打包源码 | False |
| `--no-compress` | 不创建压缩包 | False |
| `-h, --help` | 显示帮助信息 | - |

### 参数使用场景
- **`--no-venv`**: 当目标环境已有相同版本的 Python 环境时使用
- **`--no-compress`**: 快速测试打包结果时使用
- **无参数**: 完整打包，包含虚拟环境和压缩包

## 🔧 故障排除

### 常见问题



