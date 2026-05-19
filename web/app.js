let selectedScript = null;
let currentRunId = null;
let pollTimer = null;

const treeEl = document.getElementById('scriptTree');
const titleEl = document.getElementById('scriptTitle');
const pathEl = document.getElementById('scriptPath');
const formEl = document.getElementById('configForm');
const docEl = document.getElementById('doc');
const logEl = document.getElementById('log');
const statusEl = document.getElementById('status');
const runBtn = document.getElementById('runBtn');
const stopBtn = document.getElementById('stopBtn');

window.addEventListener('pywebviewready', init);
runBtn.addEventListener('click', runSelectedScript);
stopBtn.addEventListener('click', async () => {
  await window.pywebview.api.stop_current();
});

async function init() {
  const res = await window.pywebview.api.get_scripts();
  if (!res.ok) {
    treeEl.textContent = res.error;
    return;
  }
  treeEl.innerHTML = '';
  renderNodes(res.data, treeEl);
}

function renderNodes(nodes, parent) {
  nodes.forEach((node) => {
    const btn = document.createElement('button');
    btn.className = `script-item ${node.runnable ? '' : 'disabled'}`;
    btn.textContent = node.name;
    if (node.runnable) {
      btn.addEventListener('click', () => selectScript(node, btn));
    }
    parent.appendChild(btn);

    if (node.children && node.children.length) {
      const childBox = document.createElement('div');
      childBox.className = 'script-children';
      renderNodes(node.children, childBox);
      parent.appendChild(childBox);
    }
  });
}

async function selectScript(node, button) {
  document.querySelectorAll('.script-item').forEach((el) => el.classList.remove('active'));
  button.classList.add('active');
  selectedScript = node.path;
  titleEl.textContent = node.name;
  pathEl.textContent = node.path;
  logEl.textContent = '';
  statusEl.textContent = '空闲';

  const res = await window.pywebview.api.get_script_detail(node.path);
  if (!res.ok) {
    alert(res.error);
    return;
  }
  renderDoc(res.data.doc);
  renderForm(res.data.fields);
  runBtn.disabled = false;
}

function renderDoc(doc) {
  if (!doc) {
    docEl.classList.add('hidden');
    docEl.textContent = '';
    return;
  }
  docEl.textContent = doc;
  docEl.classList.remove('hidden');
}

function renderForm(fields) {
  formEl.innerHTML = '';
  fields.forEach((field) => {
    const type = normalizeType(field.type);
    if (type === 'doc') return;

    const wrap = document.createElement('div');
    wrap.className = type === 'bool' ? 'field checkbox-field' : 'field';
    const label = document.createElement('label');
    label.textContent = field.label || field.name;

    const input = createInput(field, type);
    input.dataset.name = field.name;

    if (type === 'bool') {
      wrap.appendChild(input);
      wrap.appendChild(label);
    } else {
      wrap.appendChild(label);
      wrap.appendChild(input);
    }

    if (field.description) {
      const small = document.createElement('small');
      small.textContent = field.description;
      wrap.appendChild(small);
    }
    formEl.appendChild(wrap);
  });
}

function normalizeType(type) {
  if (type === 'string') return 'text';
  return type || 'text';
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
  if (type === 'int' || type === 'float') el.type = 'number';
  else if (type === 'bool') el.type = 'checkbox';
  else if (type === 'date') el.type = 'date';
  else el.type = 'text';

  if (field.min !== undefined) el.min = field.min;
  if (field.max !== undefined) el.max = field.max;
  if (type === 'float') el.step = 'any';
  if (type === 'bool') el.checked = Boolean(field.default);
  else el.value = field.default ?? '';
  return el;
}

function collectConfig() {
  const config = {};
  formEl.querySelectorAll('[data-name]').forEach((input) => {
    const name = input.dataset.name;
    if (input.type === 'checkbox') config[name] = input.checked;
    else if (input.type === 'number') config[name] = input.value === '' ? null : Number(input.value);
    else config[name] = input.value;
  });
  return config;
}

async function runSelectedScript(event) {
  event.preventDefault();
  if (!selectedScript) return;
  runBtn.disabled = true;
  statusEl.textContent = '运行中';
  logEl.textContent = '';

  const res = await window.pywebview.api.run_script(selectedScript, collectConfig());
  if (!res.ok) {
    alert(res.error);
    runBtn.disabled = false;
    statusEl.textContent = '空闲';
    return;
  }
  currentRunId = res.data.run_id;
  pollTimer = setInterval(pollStatus, 500);
}

async function pollStatus() {
  if (!currentRunId) return;
  const res = await window.pywebview.api.get_run_status(currentRunId);
  if (!res.ok) return;
  logEl.textContent = res.data.log || '';
  logEl.scrollTop = logEl.scrollHeight;
  if (res.data.finished) {
    clearInterval(pollTimer);
    statusEl.textContent = `完成，退出码：${res.data.exit_code}`;
    runBtn.disabled = false;
  }
}
