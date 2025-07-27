# Cedar Ex 轻量化打包指南

## 打包策略

修改后的打包脚本采用**轻量化打包**策略：

### 核心思想
- **只编译代码，不打包依赖**：所有 Python 代码编译为二进制文件
- **依赖外部环境**：所有依赖库从 `my_venv/` 目录动态加载
- **最小化打包体积**：主程序只包含编译后的代码逻辑

## 打包结果

```
dist/main.dist/
├─ main.py               （编译后的主程序模块）
├─ app_ui/               （编译后的 app_ui 模块）
├─ scripts/              （编译后的脚本模块）
├─ my_venv/              （完整的虚拟环境）
├─ configs/              （配置文件目录）
├─ log/                  （日志目录）
└─ run.sh                （启动脚本）
```

## 关键修改

### 1. 使用 `--module` 模式
```bash
# 之前：--standalone（包含所有依赖）
# 现在：--module（只编译代码）
python -m nuitka --module main.py
```

### 2. 移除 `--include-package` 参数
```bash
# 之前：--include-package=PyQt5,yaml,cedar
# 现在：不包含任何包，依赖外部环境
```

### 3. 修改启动脚本
```bash
#!/bin/bash
# 设置 Python 环境
export PYTHONPATH="$PWD/app_ui:$PWD/scripts:$PYTHONPATH"
# 使用虚拟环境中的 Python 运行主程序
$PWD/my_venv/bin/python main.py
```

## 优势

1. **体积小**：主程序文件很小，只包含业务逻辑
2. **依赖清晰**：所有依赖都在 `my_venv/` 中，便于管理
3. **更新方便**：可以单独更新依赖环境而不影响代码
4. **调试友好**：可以方便地修改虚拟环境中的依赖

## 使用方法

### 1. 运行打包
```bash
python pa_simple.py
```

### 2. 运行程序
```bash
cd dist/main.dist
./run.sh
```

## 注意事项

1. **环境依赖**：程序必须依赖 `my_venv/` 目录中的 Python 环境
2. **路径固定**：启动脚本中的路径是固定的，不能随意移动
3. **权限要求**：需要确保 `my_venv/bin/python` 有执行权限

## 技术原理

### 模块模式 vs 独立模式

| 特性 | `--module` 模式 | `--standalone` 模式 |
|------|----------------|-------------------|
| 包含依赖 | ❌ 不包含 | ✅ 包含所有依赖 |
| 文件大小 | 小 | 大 |
| 运行方式 | 需要外部 Python | 完全独立 |
| 依赖管理 | 外部管理 | 内置管理 |

### 动态加载机制

1. **启动时**：`run.sh` 设置 `PYTHONPATH` 指向编译后的模块
2. **运行时**：使用 `my_venv/bin/python` 加载编译后的模块
3. **依赖解析**：Python 解释器从 `my_venv/` 中查找所有依赖包

这种打包方式既保证了代码的安全性（编译加密），又保持了部署的灵活性（依赖外部管理）。 