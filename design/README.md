# CedarEx VSCode 风格重设计图

## 设计目标

- 贴近 VSCode 的界面结构：Activity Bar、Explorer、Editor Tabs、Panel Terminal、Status Bar。
- 核心功能从“脚本列表 + 表单 + 日志”升级为“脚本工作台”。
- 支持可视化脚本操作：脚本资源树、参数表单、运行预设、历史记录、README 预览。
- 保留真实终端：底部 Terminal 使用真实 PTY，可输入命令，也承接脚本运行输出。
- 方便调用 AI：右侧 Copilot Panel 和底部 AI Review 复用当前脚本、参数、终端日志作为上下文。

## 设计图文件

- `vscode-script-workbench.html`：1440×900 静态高保真 HTML 设计图。

## 布局说明

1. 左侧 Activity Bar：脚本资源、运行、搜索、版本/历史、AI 入口。
2. Explorer：展示 `scripts/` 树、最近运行、脚本文件结构。
3. Editor 区：当前脚本的可视化参数表单，像 VSCode 编辑器标签页一样切换。
4. AI Copilot Panel：运行前检查、参数解释、模板生成、日志诊断。
5. Terminal Panel：真实终端、Problems、Output、AI Review 统一在底部面板。
6. Status Bar：工作区、AI 状态、Python 环境、编码等全局状态。

## 后续落地建议

- 第一阶段：先把现有 Web UI 改成 VSCode 外壳布局，不改变后端 API。
- 第二阶段：将 xterm 从“日志显示”升级为真实 PTY 交互终端。
- 第三阶段：增加 AI 上下文打包协议，包括当前脚本、form 值、终端最近 N 行、退出码。
