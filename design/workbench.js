const DATA = {
  tools: [
    {
      type: 'group', id: 'common', name: '常用工具', open: true, children: [
        { id: 'image', name: '图像一致性检查', desc: '检查图片尺寸、命名和数量。' },
        { id: 'rename', name: '批量重命名', desc: '按规则整理文件名，运行前会生成预览。' },
        { id: 'report', name: '结果汇总报告', desc: '把多份结果合成一份报告。' },
      ],
    },
    {
      type: 'group', id: 'dataGroup', name: '数据检查', open: true, children: [
        { id: 'data', name: '数据完整性检查', desc: '检查缺失文件和空目录。' },
        { id: 'size', name: '图片尺寸统计', desc: '统计宽高、格式和异常值。' },
        { id: 'deliver', name: '交付目录检查', desc: '检查交付目录命名规范。' },
      ],
    },
    {
      type: 'group', id: 'fileGroup', name: '文件整理', open: false, children: [
        { id: 'zip', name: '压缩包批量解压', desc: '批量解压并整理目录。' },
      ],
    },
  ],
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const state = { selectedTool: 'image', drag: null };

function renderTree() {
  const tree = $('[data-tool-tree]');
  tree.innerHTML = '';
  DATA.tools.forEach((item) => renderTreeItem(tree, item, 0));
}

function renderTreeItem(parent, item, depth) {
  const button = document.createElement('button');
  if (item.type === 'group') {
    button.className = `tree-row tree-row--group tree-row--indent-${depth}`;
    button.innerHTML = `<span class="tree-row__twisty">${item.open ? '▾' : '▸'}</span><span class="tree-row__name">${item.name}</span>`;
    button.addEventListener('click', () => {
      item.open = !item.open;
      renderTree();
    });
    parent.appendChild(button);
    if (item.open && item.children) item.children.forEach((child) => renderTreeItem(parent, child, depth + 1));
    return;
  }

  button.className = `tree-row tree-row--indent-${depth} ${state.selectedTool === item.id ? 'is-active' : ''}`;
  button.innerHTML = `<span class="tree-row__twisty"></span><span class="tree-row__name">${item.name}</span>`;
  button.addEventListener('click', () => selectTool(item.id));
  parent.appendChild(button);
}

function getTool(id) {
  const flat = flattenTools(DATA.tools);
  return flat.find((item) => item.id === id) || flat.find((item) => item.id === 'image');
}

function flattenTools(items) {
  return items.flatMap((item) => item.children ? flattenTools(item.children) : [item]);
}

function selectTool(id) {
  state.selectedTool = id;
  const tool = getTool(id);
  $('[data-doc-title]').textContent = `${tool.name} 使用说明`;
  $('[data-doc-text]').textContent = `这里展示“${tool.name}”目录下真实 README.md 的解析结果。${tool.desc}`;
  $('[data-log]').textContent = `已选择：${tool.name}。`;
  $('[data-log-state]').textContent = '等待开始。';
  renderTree();
}

function bindTabs() {
  $$('[data-view-tab]').forEach((tab) => {
    tab.addEventListener('click', () => {
      $$('[data-view-tab]').forEach((node) => node.classList.remove('is-active'));
      tab.classList.add('is-active');
      $$('[data-view]').forEach((view) => view.classList.remove('is-active'));
      $(`[data-view="${tab.dataset.viewTab}"]`).classList.add('is-active');
    });
  });
}

function bindActions() {
  $('[data-choose-folder]').addEventListener('click', () => {
    const input = $('[data-folder-input]');
    input.value = '示例数据文件夹';
    input.classList.remove('is-placeholder');
    $('[data-log]').textContent = '已选择文件夹：示例数据文件夹。可以点击底部“运行”。';
  });

  $('[data-run]').addEventListener('click', () => {
    const tool = getTool(state.selectedTool);
    $('[data-log-state]').textContent = '正在处理。';
    $('[data-log]').innerHTML = `正在运行：${tool.name}\n处理文件夹：${$('[data-folder-input]').value}\n处理方式：${$('[data-mode]').value}\n\n$ 问：请帮我分析当前执行结果\n答：已检查执行记录，当前任务处理完成。\n[完成] 处理完成。`;
    setTimeout(() => $('[data-log-state]').textContent = '处理完成。', 500);
  });

  $('[data-stop]').addEventListener('click', () => {
    $('[data-log-state]').textContent = '已请求停止。';
    $('[data-log]').textContent += '\n[停止] 已请求停止当前任务。';
  });
}

function bindResize() {
  const workbench = $('[data-workbench]');
  const shell = $('[data-shell]');
  const mainPanel = $('[data-main-panel]');
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

  $$('.splitter').forEach((bar) => {
    bar.addEventListener('pointerdown', (event) => {
      state.drag = { type: bar.dataset.resize };
      bar.classList.add('is-dragging');
      document.body.classList.add(state.drag.type === 'log' ? 'is-resizing-y' : 'is-resizing-x');
      bar.setPointerCapture(event.pointerId);
    });
  });

  window.addEventListener('pointermove', (event) => {
    if (!state.drag) return;
    if (state.drag.type === 'explorer') {
      const left = workbench.getBoundingClientRect().left;
      shell.style.gridTemplateColumns = `${clamp(event.clientX - left, 220, 420)}px 4px minmax(0,1fr)`;
    }
    if (state.drag.type === 'log') {
      const rect = mainPanel.getBoundingClientRect();
      const height = clamp(rect.bottom - 24 - event.clientY, 180, 420);
      mainPanel.style.gridTemplateRows = `36px minmax(0,1fr) 4px ${height}px`;
    }
  });

  window.addEventListener('pointerup', () => {
    if (!state.drag) return;
    $$('.splitter').forEach((bar) => bar.classList.remove('is-dragging'));
    document.body.classList.remove('is-resizing-x', 'is-resizing-y');
    state.drag = null;
  });
}

renderTree();
bindTabs();
bindActions();
bindResize();
