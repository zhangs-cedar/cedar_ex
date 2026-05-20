VS Code UI 绘制体系
├── Electron （用pywebview）
│   ├── Chromium：渲染 HTML / CSS / DOM
│   └── Node.js：本地进程、文件系统、PTY 等能力
│
├── VS Code Workbench （React替代）
│   ├── TypeScript 自研 UI 组件
│   ├── DOM API
│   ├── CSS
│   └── 自己的布局、事件、主题、命令系统
│
├── Monaco Editor （不用）
│   └── 代码编辑器核心
│
├── xterm.js
│   └── 终端前端渲染
│
└── node-pty
    └── 终端后端 PTY


pywebview + WebView2
+ React/TypeScript 自己实现轻量 Workbench
+ Monaco Editor
+ xterm.js
+ Python 后端