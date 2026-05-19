const state = {
  scripts: [],
  flatScripts: [],
  selectedPath: null,
  selectedNode: null,
  fields: [],
  defaults: {},
  runId: null,
  polling: null,
  running: false,
  docCollapsed: false,
};

const $ = (id) => document.getElementById(id);
const els = {
  tree: $('scriptTree'),
  search: $('scriptSearch'),
  count: $('scriptCount'),
  refresh: $('refreshBtn'),
  title: $('taskName'),
  path: $('scriptPath'),
  state: $('runState'),
  empty: $('emptyState'),
  task: $('taskPanel'),
  form: $('configForm'),
  doc: $('doc'),
  run: $('runBtn'),
  stop: $('stopBtn'),
  log: $('terminal'),
  logHint: $('logHint'),
  analyze: $('analyzeBtn'),
  aiReviewPanel: $('aiReviewPanel'),
  aiReview: $('aiReview'),
  toggleDoc: $('toggleDocBtn'),
  readmePanel: $('readmePanel'),
  terminalTitle: $('terminalTitle'),
  toast: $('toast'),
  sideTitle: $('sideTitle'),
  sidePanel: $('sidePanel'),
  precheck: $('precheckText'),
};
let term = null;
let terminalPoller = null;
let terminalTranscript = '';

window.addEventListener('pywebviewready', init);
if (window.mermaid) {
  window.mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'default' });
}
els.search.addEventListener('input', () => renderTree());
els.refresh.addEventListener('click', init);
els.run.addEventListener('click', runSelectedScript);
els.stop.addEventListener('click', stopCurrentScript);
if (els.analyze) els.analyze.addEventListener('click', analyzeCurrentRun);
els.toggleDoc.addEventListener('click', toggleDoc);
document.querySelectorAll('[data-ai-action]').forEach((btn) => {
  btn.addEventListener('click', () => runAiQuickAction(btn.dataset.aiAction, btn));
});
document.querySelectorAll('[data-view]').forEach((btn) => {
  btn.addEventListener('click', () => switchActivityView(btn.dataset.view));
});
document.querySelectorAll('[data-editor-tab]').forEach((btn) => {
  btn.addEventListener('click', () => switchEditorTab(btn.dataset.editorTab));
});

async function init() {
  setRunState('loading', '加载中');
  await initTerminal();
  els.stop.disabled = false;
  const res = await window.pywebview.api.get_scripts();
  if (!res.ok) {
    showToast(res.error || '脚本加载失败');
    setRunState('error', '加载失败');
    return;
  }
  state.scripts = res.data || [];
  state.flatScripts = flattenScripts(state.scripts);
  els.count.textContent = `${state.flatScripts.length} 个工具`;
  renderTree();
  setRunState('idle', '空闲');
  setTerminalTitle('空闲');
}

async function switchActivityView(view) {
  document.querySelectorAll('[data-view]').forEach((btn) => btn.classList.toggle('active', btn.dataset.view === view));
  els.tree.classList.toggle('hidden', view !== 'explorer' && view !== 'search');
  els.search.parentElement.classList.toggle('hidden', !['explorer', 'search'].includes(view));
  els.sidePanel.classList.toggle('hidden', view === 'explorer' || view === 'search');
  const titles = { explorer: '工具列表', run: '运行工具', search: '搜索工具', history: '运行记录', ai: '智能助手' };
  els.sideTitle.textContent = titles[view] || '工具列表';
  if (view === 'search') {
    els.search.focus();
    return;
  }
  if (view === 'run') renderSidePanel([
    sideCard('当前工具', state.selectedNode ? state.selectedNode.name : '尚未选择工具', state.selectedPath ? '可以点击底部运行，也可以随时停止。' : '请先在工具列表中选择一个工具。', '运行选中工具', () => els.run.click()),
    sideCard('执行过程', '底部会显示执行记录', '运行中的输出会实时显示，方便复制给他人排查。', '查看执行过程', () => term?.focus()),
  ]);
  if (view === 'ai') renderSidePanel([
    sideCard('智能助手', '工具 + 填写信息 + 使用说明 + 执行记录', '右侧快捷动作会自动带上当前上下文。', '查看问题原因', () => runAiQuickAction('diagnose_log', document.querySelector('[data-ai-action="diagnose_log"]'))),
    sideCard('建议', '先运行工具，再查看智能建议', '这样助手能看到真实输出、错误和退出信息。', '打开智能建议', () => els.aiReviewPanel.classList.remove('hidden')),
  ]);
  if (view === 'history') await renderHistoryPanel();
}

function switchEditorTab(tab) {
  document.querySelectorAll('[data-editor-tab]').forEach((btn) => btn.classList.toggle('active', btn.dataset.editorTab === tab));
  els.empty.classList.toggle('hidden', tab !== 'form' || Boolean(state.selectedPath));
  els.task.classList.toggle('hidden', tab !== 'form' || !state.selectedPath);
  els.readmePanel.classList.toggle('hidden', tab !== 'readme');
}

function sideCard(title, headline, text, actionText, onClick) {
  const card = document.createElement('div');
  card.className = 'side-card';
  card.innerHTML = `<b>${escapeHtml(title)}</b><p><strong>${escapeHtml(headline)}</strong></p><p>${escapeHtml(text)}</p>`;
  if (actionText) {
    const btn = document.createElement('button');
    btn.textContent = actionText;
    btn.addEventListener('click', onClick);
    card.appendChild(btn);
  }
  return card;
}

function renderSidePanel(nodes) {
  els.sidePanel.innerHTML = '';
  nodes.forEach((node) => els.sidePanel.appendChild(node));
}

async function renderHistoryPanel() {
  els.sidePanel.innerHTML = '<div class="side-card"><p>正在加载最近日志...</p></div>';
  const res = await window.pywebview.api.get_recent_logs(20);
  if (!res.ok) {
    els.sidePanel.innerHTML = `<div class="side-card"><p>${escapeHtml(res.error || '加载失败')}</p></div>`;
    return;
  }
  els.sidePanel.innerHTML = '';
  if (!res.data.length) {
    els.sidePanel.innerHTML = '<div class="side-card"><p>暂无历史日志。</p></div>';
    return;
  }
  res.data.forEach((item) => {
    const btn = document.createElement('button');
    btn.className = 'history-item';
    btn.innerHTML = `${escapeHtml(item.path)}<small>${escapeHtml(item.modified)} · ${Math.round(item.size / 1024)} KB</small>`;
    btn.addEventListener('click', () => openRunDetail(item.path));
    els.sidePanel.appendChild(btn);
  });
}

async function openRunDetail(logPath) {
  els.aiReviewPanel.classList.remove('hidden');
  els.aiReview.innerHTML = '<p>正在加载运行详情...</p>';
  const res = await window.pywebview.api.get_log_detail(logPath, 120000);
  if (!res.ok) {
    els.aiReview.innerHTML = renderMarkdown(`运行详情加载失败：${res.error || '未知错误'}`);
    return;
  }
  const item = res.data;
  const clipped = item.clipped ? '\n\n> 日志较长，当前仅展示最后一部分。' : '';
  els.aiReview.innerHTML = renderMarkdown(`### Run Detail: ${item.path}\n\n- 修改时间：${item.modified}\n- 文件大小：${Math.round(item.size / 1024)} KB${clipped}\n\n\`\`\`text\n${item.content || '日志为空'}\n\`\`\``);
  terminalTranscript = item.content || terminalTranscript;
  if (els.analyze) els.analyze.disabled = false;
}

function flattenScripts(nodes, list = []) {
  nodes.forEach((node) => {
    if (node.runnable) list.push(node);
    flattenScripts(node.children || [], list);
  });
  return list;
}

function renderTree() {
  const keyword = els.search.value.trim().toLowerCase();
  els.tree.innerHTML = '';
  const fragment = document.createDocumentFragment();
  const visibleCount = renderNodes(state.scripts, fragment, keyword);
  if (visibleCount === 0) {
    const empty = document.createElement('div');
    empty.className = 'no-result';
    empty.textContent = '没有找到匹配的工具';
    fragment.appendChild(empty);
  }
  els.tree.appendChild(fragment);
}

function renderNodes(nodes, parent, keyword) {
  let visibleCount = 0;
  nodes.forEach((node) => {
    const childrenBox = document.createElement('div');
    childrenBox.className = 'script-children';
    const childVisible = renderNodes(node.children || [], childrenBox, keyword);
    const selfMatched = !keyword || node.name.toLowerCase().includes(keyword) || node.path.toLowerCase().includes(keyword);
    const visible = selfMatched || childVisible > 0;
    if (!visible) return;

    const btn = document.createElement('button');
    btn.className = `script-item ${node.runnable ? 'tool-item' : 'folder-item disabled'} ${state.selectedPath === node.path ? 'active' : ''}`;
    btn.title = node.path || node.name;
    btn.innerHTML = node.runnable
      ? `<span class="script-name">${escapeHtml(node.name)}</span><small>${escapeHtml(node.path || '可运行工具')}</small>`
      : `<span class="script-name">▾ ${escapeHtml(node.name)}</span>`;
    if (node.runnable) btn.addEventListener('click', () => selectScript(node));
    parent.appendChild(btn);
    if (childVisible > 0) parent.appendChild(childrenBox);
    visibleCount += node.runnable ? 1 : childVisible;
  });
  return visibleCount;
}

async function selectScript(node) {
  if (state.running) {
    showToast('工具运行中，请结束后再切换');
    return;
  }
  state.selectedPath = node.path;
  state.selectedNode = node;
  renderTree();
  setLog('');
  setRunState('idle', '空闲');
  setTerminalTitle(`已选择 ${node.name}`);
  els.title.textContent = node.name;
  els.path.textContent = node.path;
  if (els.precheck) els.precheck.textContent = '请确认必填信息已填写，然后点击底部“运行”。';
  els.empty.classList.add('hidden');
  els.task.classList.remove('hidden');
  els.readmePanel.classList.add('hidden');
  document.querySelectorAll('[data-editor-tab]').forEach((btn) => btn.classList.toggle('active', btn.dataset.editorTab === 'form'));

  const res = await window.pywebview.api.get_script_detail(node.path);
  if (!res.ok) {
    showToast(res.error || '读取脚本详情失败');
    return;
  }
  state.fields = res.data.fields || [];
  state.defaults = Object.fromEntries(state.fields.map((field) => [field.name, field.default]));
  renderDoc(res.data.doc);
  renderForm(state.fields);
}

function renderDoc(doc) {
  els.doc.innerHTML = doc ? renderMarkdown(doc) : '<p>暂无使用说明。</p>';
  els.doc.classList.toggle('hidden', state.docCollapsed);
  els.toggleDoc.textContent = state.docCollapsed ? '展开' : '收起';
  renderMermaidDiagrams();
}

function toggleDoc() {
  state.docCollapsed = !state.docCollapsed;
  els.doc.classList.toggle('hidden', state.docCollapsed);
  els.toggleDoc.textContent = state.docCollapsed ? '展开' : '收起';
}

function renderForm(fields) {
  els.form.innerHTML = '';
  if (!fields.length) {
    const empty = document.createElement('div');
    empty.className = 'field full';
    empty.innerHTML = '<small>该工具没有需要填写的信息，点击底部“运行”即可执行。</small>';
    els.form.appendChild(empty);
    return;
  }
  fields.forEach((field) => {
    const type = normalizeType(field.type);
    if (type === 'doc') return;
    const wrap = document.createElement('div');
    wrap.className = `field ${['multiline', 'file', 'dir'].includes(type) ? 'full' : ''} ${type === 'bool' ? 'checkbox-field' : ''}`;
    const input = createInput(field, type);
    if (!input.classList || !input.classList.contains('picker-row')) {
      input.dataset.name = field.name;
      input.dataset.type = type;
    }

    const label = document.createElement('label');
    label.innerHTML = `${escapeHtml(field.label || field.name)}${field.required ? '<span class="required">*</span>' : ''}`;

    if (type === 'bool') {
      const copy = document.createElement('div');
      copy.className = 'checkbox-copy';
      copy.appendChild(label);
      if (field.description) copy.appendChild(helpText(field.description));
      wrap.appendChild(input);
      wrap.appendChild(copy);
    } else {
      wrap.appendChild(label);
      wrap.appendChild(input);
      if (field.description) wrap.appendChild(helpText(field.description));
    }
    els.form.appendChild(wrap);
  });
}

function createInput(field, type) {
  if (type === 'multiline') {
    const el = document.createElement('textarea');
    el.value = field.default ?? '';
    return el;
  }
  if (type === 'select') {
    const el = document.createElement('select');
    (field.options || []).forEach((option) => {
      const opt = document.createElement('option');
      opt.value = String(option);
      opt.textContent = String(option);
      el.appendChild(opt);
    });
    el.value = field.default ?? '';
    return el;
  }
  if (type === 'file' || type === 'dir') {
    return createPathPicker(field, type);
  }
  const el = document.createElement('input');
  el.type = type === 'int' || type === 'float' ? 'number' : type === 'bool' ? 'checkbox' : type === 'date' ? 'date' : 'text';
  if (field.min !== undefined) el.min = field.min;
  if (field.max !== undefined) el.max = field.max;
  if (type === 'float') el.step = 'any';
  if (type === 'bool') el.checked = Boolean(field.default);
  else el.value = field.default ?? '';
  return el;
}

function createPathPicker(field, type) {
  const row = document.createElement('div');
  row.className = 'picker-row';
  const input = document.createElement('input');
  input.type = 'text';
  input.value = field.default ?? '';
  input.placeholder = type === 'dir' ? '请选择或输入本地目录路径' : '请选择或输入本地文件路径';
  input.dataset.name = field.name;
  input.dataset.type = type;

  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'ghost';
  btn.textContent = type === 'dir' ? '选择目录' : '选择文件';
  btn.addEventListener('click', async () => {
    const res = type === 'dir'
      ? await window.pywebview.api.choose_directory()
      : await window.pywebview.api.choose_file();
    if (res.ok && res.data) input.value = res.data;
    else if (!res.ok) showToast(res.error || '选择失败');
  });

  row.appendChild(input);
  row.appendChild(btn);
  return row;
}

function helpText(text) {
  const small = document.createElement('small');
  small.textContent = text;
  return small;
}

function normalizeType(type) {
  if (type === 'string') return 'text';
  return type || 'text';
}

function collectConfig() {
  const config = {};
  els.form.querySelectorAll('[data-name]').forEach((input) => {
    const name = input.dataset.name;
    const type = input.dataset.type;
    if (type === 'bool') config[name] = input.checked;
    else if (type === 'int') config[name] = input.value === '' ? null : parseInt(input.value, 10);
    else if (type === 'float') config[name] = input.value === '' ? null : Number(input.value);
    else config[name] = input.value;
  });
  return config;
}

function validateForm() {
  for (const field of state.fields) {
    if (!field.required) continue;
    const input = els.form.querySelector(`[data-name="${cssEscape(field.name)}"]`);
    if (!input || input.type === 'checkbox') continue;
    if (String(input.value || '').trim() === '') {
      showToast(`请填写：${field.label || field.name}`);
      input.focus();
      return false;
    }
  }
  return true;
}

async function runSelectedScript(event) {
  event.preventDefault();
  if (!state.selectedPath || state.running || !validateForm()) return;
  setRunning(true);
  setRunState('running', '运行中');
  setTerminalTitle(`正在运行 ${state.selectedPath}`);
  setLog(`正在启动：${state.selectedNode?.name || state.selectedPath}\n`);
  const res = await window.pywebview.api.run_script(state.selectedPath, collectConfig());
  if (!res.ok) {
    setRunning(false);
    setRunState('error', '启动失败');
    setTerminalTitle('启动失败');
    showToast(res.error || '启动失败');
    return;
  }
  state.runId = null;
  if (els.analyze) els.analyze.disabled = false;
  els.aiReviewPanel.classList.add('hidden');
  setRunning(false);
  setRunState('running', '已开始');
  showToast('工具已开始执行');
}

async function analyzeCurrentRun() {
  if (!state.runId && !terminalTranscript.trim()) return showToast('暂无可分析的终端内容');
  if (els.analyze) els.analyze.disabled = true;
  els.aiReviewPanel.classList.remove('hidden');
  els.aiReview.innerHTML = '<p>opencode 正在分析本次运行，请稍候...</p>';
  const res = state.runId
    ? await window.pywebview.api.analyze_run_with_opencode(state.runId)
    : await window.pywebview.api.analyze_terminal_with_opencode(state.selectedPath, collectConfig(), terminalTranscript);
  if (res.ok) {
    els.aiReview.innerHTML = renderMarkdown(res.data.review || 'opencode 未返回分析内容。');
    renderMermaidDiagrams();
    showToast('opencode 分析完成');
  } else {
    const review = res.data?.review ? `\n\n${res.data.review}` : '';
    els.aiReview.innerHTML = renderMarkdown(`分析失败：${res.error}${review}`);
    showToast(res.error || 'opencode 分析失败');
  }
  if (els.analyze) els.analyze.disabled = false;
}

async function runAiQuickAction(action, button) {
  if (!window.pywebview?.api?.ai_assist) return showToast('AI 助手接口不可用');
  button.disabled = true;
  els.aiReviewPanel.classList.remove('hidden');
  els.aiReview.innerHTML = '<p>opencode 正在处理快捷动作，请稍候...</p>';
  const docText = els.doc.innerText || '';
  const res = await window.pywebview.api.ai_assist({
    action,
    script_path: state.selectedPath,
    script_name: state.selectedNode?.name || '',
    fields: state.fields,
    config: collectConfig(),
    doc: docText,
    terminal_log: terminalTranscript,
  });
  if (res.ok) {
    els.aiReview.innerHTML = renderMarkdown(res.data.review || 'opencode 未返回内容。');
    renderMermaidDiagrams();
    showToast('AI 快捷动作完成');
  } else {
    const review = res.data?.review ? `\n\n${res.data.review}` : '';
    els.aiReview.innerHTML = renderMarkdown(`AI 快捷动作失败：${res.error}${review}`);
    showToast(res.error || 'AI 快捷动作失败');
  }
  button.disabled = false;
}

async function stopCurrentScript() {
  const res = await window.pywebview.api.stop_current();
  setRunning(false);
  setRunState('idle', '已停止');
  els.logHint.textContent = '已请求停止。';
  showToast(res.data || res.error || '已请求停止');
}

function setRunning(running) {
  state.running = running;
  els.run.disabled = running;
  els.stop.disabled = false;
  els.search.disabled = running;
}

function setRunState(kind, text) {
  els.state.className = `run-state ${kind === 'running' ? 'running' : kind === 'success' ? 'success' : kind === 'error' ? 'error' : ''}`;
  els.state.textContent = text;
}

function setLog(text) {
  terminalTranscript = text || '';
  if (term) {
    term.clear();
    if (terminalTranscript) term.write(terminalTranscript.replace(/\n/g, '\r\n'));
  }
  els.logHint.textContent = text ? '执行记录正在更新。' : '等待开始。';
}

function appendTerminal(text) {
  terminalTranscript += text;
  if (term) term.write(text.replace(/\n/g, '\r\n'));
  els.logHint.textContent = '执行记录已更新。';
  updateCompletionFromOutput();
}

async function initTerminal() {
  if (!window.Terminal || term) return;
  term = new window.Terminal({
    cursorBlink: true,
    convertEol: true,
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
    fontSize: 13,
    theme: { background: '#fbfbfb', foreground: '#24292f', cursor: '#0969da', selectionBackground: '#0969da33' },
  });
  term.open(els.log);
  const cols = term.cols || 100;
  const rows = term.rows || 30;
  const started = await window.pywebview.api.terminal_start(cols, rows);
  if (!started.ok) {
    term.write(`执行环境启动失败: ${started.error}\r\n`);
    return;
  }
  setTerminalTitle(`执行环境已就绪`);
  if (els.analyze) els.analyze.disabled = false;
  term.onData((data) => window.pywebview.api.terminal_write(data));
  terminalPoller = setInterval(async () => {
    const res = await window.pywebview.api.terminal_read();
    if (res.ok && res.data) {
      terminalTranscript += res.data;
      term.write(res.data);
      els.logHint.textContent = '执行记录已更新。';
      updateCompletionFromOutput();
    }
  }, 50);
  window.addEventListener('resize', resizeTerminal);
  setTimeout(resizeTerminal, 100);
}

async function resizeTerminal() {
  if (!term) return;
  const charWidth = 8;
  const charHeight = 17;
  const rect = els.log.getBoundingClientRect();
  const cols = Math.max(40, Math.floor((rect.width - 20) / charWidth));
  const rows = Math.max(10, Math.floor((rect.height - 20) / charHeight));
  term.resize(cols, rows);
  await window.pywebview.api.terminal_resize(cols, rows);
}

function setTerminalTitle(text) {
  if (els.terminalTitle) els.terminalTitle.textContent = `cedarex — ${text}`;
}

function updateCompletionFromOutput() {
  if (!state.selectedPath || !terminalTranscript) return;
  const lower = terminalTranscript.toLowerCase();
  const completed = /\n\$\s*$|process finished|exit code|退出码|completed|完成|success|成功/.test(lower);
  if (!completed || state.running) return;
  setRunState('success', '已完成');
  els.logHint.textContent = '处理完成。';
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.remove('hidden');
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => els.toast.classList.add('hidden'), 2600);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
}

function renderMarkdown(markdown) {
  const lines = String(markdown).replace(/\r\n/g, '\n').split('\n');
  const html = [];
  let inCode = false;
  let codeLang = '';
  let codeLines = [];
  let listType = null;
  let paragraph = [];

  const flushParagraph = () => {
    if (paragraph.length) {
      html.push(`<p>${renderInline(paragraph.join(' '))}</p>`);
      paragraph = [];
    }
  };
  const closeList = () => {
    if (listType) {
      html.push(`</${listType}>`);
      listType = null;
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (line.startsWith('```')) {
      if (inCode) {
        const codeText = codeLines.join('\n');
        if (codeLang === 'mermaid') {
          html.push(`<div class="mermaid">${escapeHtml(codeText)}</div>`);
        } else {
          html.push(`<pre><code>${escapeHtml(codeText)}</code></pre>`);
        }
        inCode = false;
        codeLang = '';
        codeLines = [];
      } else {
        flushParagraph();
        closeList();
        inCode = true;
        codeLang = line.replace(/^```/, '').trim().toLowerCase();
      }
      continue;
    }
    if (inCode) {
      codeLines.push(rawLine);
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      closeList();
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      closeList();
      const level = heading[1].length;
      html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
      continue;
    }

    const quote = line.match(/^>\s?(.+)$/);
    if (quote) {
      flushParagraph();
      closeList();
      html.push(`<blockquote>${renderInline(quote[1])}</blockquote>`);
      continue;
    }

    const unordered = line.match(/^[-*]\s+(.+)$/);
    const ordered = line.match(/^\d+\.\s+(.+)$/);
    if (unordered || ordered) {
      flushParagraph();
      const tag = unordered ? 'ul' : 'ol';
      if (listType !== tag) {
        closeList();
        html.push(`<${tag}>`);
        listType = tag;
      }
      html.push(`<li>${renderInline((unordered || ordered)[1])}</li>`);
      continue;
    }

    if (/^\|.+\|$/.test(line)) {
      flushParagraph();
      closeList();
      html.push(renderTableLine(line));
      continue;
    }

    paragraph.push(line.trim());
  }
  flushParagraph();
  closeList();
  if (inCode) {
    const codeText = codeLines.join('\n');
    html.push(codeLang === 'mermaid' ? `<div class="mermaid">${escapeHtml(codeText)}</div>` : `<pre><code>${escapeHtml(codeText)}</code></pre>`);
  }
  return html.join('\n').replace(/<\/table>\n<table>/g, '');
}

async function renderMermaidDiagrams() {
  if (!window.mermaid) return;
  const nodes = Array.from(els.doc.querySelectorAll('.mermaid'));
  for (const node of nodes) {
    const source = node.textContent || '';
    const id = `mermaid-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    try {
      const result = await window.mermaid.render(id, source);
      node.innerHTML = result.svg;
      if (result.bindFunctions) result.bindFunctions(node);
    } catch (error) {
      node.className = 'mermaid-error';
      node.innerHTML = `<strong>流程图渲染失败</strong><p>README.md 中的 Mermaid 图表语法不兼容当前版本。</p><pre>${escapeHtml(source)}</pre>`;
      showToast('流程图渲染失败，请检查 README.md 中的 Mermaid 语法');
    }
  }
}

function renderInline(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2">$1</a>');
}

function renderTableLine(line) {
  if (/^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line)) return '';
  const cells = line.split('|').slice(1, -1).map((cell) => `<td>${renderInline(cell.trim())}</td>`).join('');
  return `<table><tr>${cells}</tr></table>`;
}

function cssEscape(value) {
  if (window.CSS && window.CSS.escape) return window.CSS.escape(value);
  return String(value).replace(/"/g, '\\"');
}
