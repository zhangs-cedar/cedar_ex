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
  title: $('scriptTitle'),
  path: $('scriptPath'),
  state: $('runState'),
  empty: $('emptyState'),
  task: $('taskPanel'),
  form: $('configForm'),
  doc: $('doc'),
  run: $('runBtn'),
  stop: $('stopBtn'),
  reset: $('resetBtn'),
  log: $('log'),
  logHint: $('logHint'),
  clearLog: $('clearLogBtn'),
  copyLog: $('copyLogBtn'),
  toggleDoc: $('toggleDocBtn'),
  toast: $('toast'),
};

window.addEventListener('pywebviewready', init);
els.search.addEventListener('input', () => renderTree());
els.refresh.addEventListener('click', init);
els.run.addEventListener('click', runSelectedScript);
els.stop.addEventListener('click', stopCurrentScript);
els.reset.addEventListener('click', resetForm);
els.clearLog.addEventListener('click', () => setLog(''));
els.copyLog.addEventListener('click', copyLog);
els.toggleDoc.addEventListener('click', toggleDoc);

async function init() {
  setRunState('loading', '加载中');
  const res = await window.pywebview.api.get_scripts();
  if (!res.ok) {
    showToast(res.error || '脚本加载失败');
    setRunState('error', '加载失败');
    return;
  }
  state.scripts = res.data || [];
  state.flatScripts = flattenScripts(state.scripts);
  els.count.textContent = `${state.flatScripts.length} 个可运行脚本`;
  renderTree();
  setRunState('idle', '空闲');
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
    empty.textContent = '没有找到匹配的脚本';
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
    btn.className = `script-item ${node.runnable ? '' : 'disabled'} ${state.selectedPath === node.path ? 'active' : ''}`;
    btn.title = node.path || node.name;
    btn.innerHTML = `<span class="script-icon">${node.runnable ? '▶' : '▾'}</span><span class="script-name">${escapeHtml(node.name)}</span>`;
    if (node.runnable) btn.addEventListener('click', () => selectScript(node));
    parent.appendChild(btn);
    if (childVisible > 0) parent.appendChild(childrenBox);
    visibleCount += node.runnable ? 1 : childVisible;
  });
  return visibleCount;
}

async function selectScript(node) {
  if (state.running) {
    showToast('脚本运行中，请结束后再切换');
    return;
  }
  state.selectedPath = node.path;
  state.selectedNode = node;
  renderTree();
  setLog('');
  setRunState('idle', '空闲');
  els.title.textContent = node.name;
  els.path.textContent = node.path;
  els.empty.classList.add('hidden');
  els.task.classList.remove('hidden');

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
  els.doc.textContent = doc || '暂无说明文档。';
  els.doc.classList.toggle('hidden', state.docCollapsed);
  els.toggleDoc.textContent = state.docCollapsed ? '展开' : '收起';
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
    empty.innerHTML = '<small>该脚本没有参数配置，点击“运行脚本”即可执行。</small>';
    els.form.appendChild(empty);
    return;
  }
  fields.forEach((field) => {
    const type = normalizeType(field.type);
    if (type === 'doc') return;
    const wrap = document.createElement('div');
    wrap.className = `field ${['multiline', 'file', 'dir'].includes(type) ? 'full' : ''} ${type === 'bool' ? 'checkbox-field' : ''}`;
    const input = createInput(field, type);
    input.dataset.name = field.name;
    input.dataset.type = type;

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
  const el = document.createElement('input');
  el.type = type === 'int' || type === 'float' ? 'number' : type === 'bool' ? 'checkbox' : type === 'date' ? 'date' : 'text';
  if (field.min !== undefined) el.min = field.min;
  if (field.max !== undefined) el.max = field.max;
  if (type === 'float') el.step = 'any';
  if (type === 'bool') el.checked = Boolean(field.default);
  else el.value = field.default ?? '';
  return el;
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
  setLog('正在启动脚本...\n');
  const res = await window.pywebview.api.run_script(state.selectedPath, collectConfig());
  if (!res.ok) {
    setRunning(false);
    setRunState('error', '启动失败');
    showToast(res.error || '启动失败');
    return;
  }
  state.runId = res.data.run_id;
  state.polling = setInterval(pollStatus, 500);
}

async function pollStatus() {
  if (!state.runId) return;
  const res = await window.pywebview.api.get_run_status(state.runId);
  if (!res.ok) return;
  setLog(res.data.log || '');
  if (res.data.finished) {
    clearInterval(state.polling);
    state.polling = null;
    setRunning(false);
    const ok = res.data.exit_code === 0;
    setRunState(ok ? 'success' : 'error', ok ? '执行成功' : `失败：${res.data.exit_code}`);
    showToast(ok ? '脚本执行完成' : '脚本执行失败，请查看日志');
  }
}

async function stopCurrentScript() {
  if (!state.running) return;
  const res = await window.pywebview.api.stop_current();
  showToast(res.data || res.error || '已请求停止');
}

function resetForm() {
  renderForm(state.fields);
  showToast('参数已恢复默认值');
}

function setRunning(running) {
  state.running = running;
  els.run.disabled = running;
  els.stop.disabled = !running;
  els.reset.disabled = running;
  els.search.disabled = running;
}

function setRunState(kind, text) {
  els.state.className = `run-state ${kind === 'running' ? 'running' : kind === 'success' ? 'success' : kind === 'error' ? 'error' : ''}`;
  els.state.textContent = text;
}

function setLog(text) {
  els.log.textContent = text;
  els.log.scrollTop = els.log.scrollHeight;
  els.logHint.textContent = text ? '日志实时更新中。' : '运行脚本后日志会显示在这里。';
}

async function copyLog() {
  const text = els.log.textContent;
  if (!text) return showToast('暂无日志可复制');
  try {
    await navigator.clipboard.writeText(text);
    showToast('日志已复制');
  } catch {
    showToast('复制失败，可手动选中日志复制');
  }
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

function cssEscape(value) {
  if (window.CSS && window.CSS.escape) return window.CSS.escape(value);
  return String(value).replace(/"/g, '\\"');
}
