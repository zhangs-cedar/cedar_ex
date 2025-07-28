# Tools 工具目录

这个目录包含了项目的各种工具脚本。

## 文件说明

### pa_mac.py
**Nuitka 打包工具**

用于将 Cedar Ex 项目打包成可执行程序。

#### 功能特性
- ✅ 轻量化打包策略
- ✅ 代码加密保护
- ✅ 插件兼容性支持
- ✅ 智能目录过滤
- ✅ 自动启动脚本生成

#### 使用方法
```bash
# 在项目根目录下运行
python tools/pa_mac.py

# 或者进入 tools 目录运行
cd tools
python pa_mac.py
```

#### 打包结果
```
dist/main.dist/
├─ main.cpython-310-darwin.so    （编译后的主程序模块）
├─ app_ui/                        （编译后的 app_ui 模块）
├─ scripts/                       （编译后的脚本模块）
├─ my_venv/                       （完整的虚拟环境）
├─ log/                           （日志目录）
└─ run.sh                         （启动脚本）
```

#### 运行打包后的程序
```bash
cd dist/main.dist
./run.sh
```

## 注意事项

1. **路径兼容性**: 脚本已优化，支持从项目根目录或 tools 目录运行
2. **环境要求**: 需要 `/opt/homebrew/anaconda3/envs/py310` conda 环境
3. **依赖管理**: 使用外部虚拟环境，保持打包体积小
4. **代码安全**: 所有 Python 代码都编译为 `.so` 文件加密保护 