# CedarEx 当前效果设计图

## 设计目标

- 按当前实现截图重生成 VSCode 风格脚本工作台空状态。
- 保留真实界面结构：Activity Bar、脚本资源管理器、编辑区标签、AI Copilot Panel、Terminal Panel、Status Bar。
- 强调当前状态：未加载脚本、中心引导选择脚本、终端处于 idle、AI 快捷动作可见。

## 设计图文件

- `vscode-script-workbench.html`：1440x900 静态高保真 HTML 设计图。

## 布局说明

1. 左侧 Activity Bar：脚本、运行、搜索、辅助入口和 AI 固定入口。
2. Explorer：显示脚本资源管理器、搜索框、脚本数量和刷新入口。
3. Editor：默认空状态，引导用户选择脚本、填写参数并运行。
4. AI Copilot Panel：展示脚本说明空态和快捷动作。
5. Terminal Panel：底部真实 PTY 面板，包含 TERMINAL/PROBLEMS/OUTPUT/AI REVIEW 标签和日志操作按钮。
6. Status Bar：展示 CedarEx Workspace、AI 状态和编码信息。
