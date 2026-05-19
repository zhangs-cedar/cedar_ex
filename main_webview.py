import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / 'scripts'
WEB_DIR = BASE_DIR / 'web'
LOG_DIR = BASE_DIR / 'log'


def should_skip_directory(dir_name):
    skip_patterns = {'.build', '__pycache__', '.git', '.svn', '.hg', 'node_modules', '.vscode', '.idea'}
    return dir_name in skip_patterns or dir_name.endswith('.build')


def get_script_file_path(script_dir):
    main_py = script_dir / 'main.py'
    if main_py.exists():
        return main_py

    for file_path in script_dir.iterdir():
        name = file_path.name
        if (name.startswith('main.cpython-') or name.startswith('main.cp')) and name.endswith(('.so', '.pyd')):
            return file_path
    return None


def has_script_file(script_dir):
    return script_dir.is_dir() and get_script_file_path(script_dir) is not None


def has_valid_subdirs(dir_path):
    try:
        return any(p.is_dir() and not should_skip_directory(p.name) for p in dir_path.iterdir())
    except OSError:
        return False


class ScriptRun:
    def __init__(self, run_id, process, log_path, config_path):
        self.run_id = run_id
        self.process = process
        self.log_path = log_path
        self.config_path = config_path
        self.created_at = datetime.now().isoformat(timespec='seconds')
        self.finished = False
        self.exit_code = None


class Api:
    def __init__(self):
        LOG_DIR.mkdir(exist_ok=True)
        self.runs = {}
        self.current_run = None

    def get_scripts(self):
        """返回脚本树。只有包含 main.py/.pyd/.so 的节点可运行。"""
        def build_node(path, rel_parts):
            children = []
            try:
                entries = sorted(path.iterdir(), key=lambda p: p.name)
            except OSError:
                entries = []

            for entry in entries:
                if not entry.is_dir() or should_skip_directory(entry.name):
                    continue
                if has_script_file(entry) or has_valid_subdirs(entry):
                    child = build_node(entry, rel_parts + [entry.name])
                    if child['runnable'] or child['children']:
                        children.append(child)

            script_file = get_script_file_path(path) if path.exists() else None
            rel_path = '/'.join(rel_parts)
            return {
                'name': path.name if rel_parts else 'scripts',
                'path': rel_path,
                'runnable': script_file is not None,
                'children': children,
            }

        if not SCRIPTS_DIR.exists():
            return {'ok': False, 'error': f'脚本目录不存在: {SCRIPTS_DIR}', 'data': []}
        return {'ok': True, 'data': build_node(SCRIPTS_DIR, [])['children']}

    def get_script_detail(self, script_rel_path):
        script_dir = self._safe_script_dir(script_rel_path)
        if not script_dir or not has_script_file(script_dir):
            return {'ok': False, 'error': '脚本不存在或不可运行'}

        form_path = script_dir / 'form.yaml'
        fields = []
        if form_path.exists():
            with form_path.open('r', encoding='utf-8') as f:
                form_cfg = yaml.safe_load(f) or {}
            fields = form_cfg.get('fields', []) or []

        readme_path = script_dir / 'README.md'
        doc = ''
        if readme_path.exists():
            doc = readme_path.read_text(encoding='utf-8').strip()

        return {'ok': True, 'data': {'path': script_rel_path, 'fields': fields, 'doc': doc}}

    def run_script(self, script_rel_path, config):
        if self.current_run and self.current_run.process.poll() is None:
            return {'ok': False, 'error': '已有脚本正在运行，请等待结束或先停止'}

        script_dir = self._safe_script_dir(script_rel_path)
        if not script_dir or not has_script_file(script_dir):
            return {'ok': False, 'error': '脚本不存在或不可运行'}

        script_path = get_script_file_path(script_dir)
        config_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
        json.dump(config or {}, config_file, ensure_ascii=False, indent=2)
        config_file.close()

        run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_path = LOG_DIR / f'webview_{run_id}.log'
        env = os.environ.copy()
        env['SCRIPT_LOG_FILE'] = str(log_path)
        env['CEDAR_BASE_DIR'] = str(BASE_DIR)

        if str(script_path).endswith(('.so', '.pyd')):
            cmd = [sys.executable, '-c', self._compiled_runner_code(script_dir, config_file.name)]
        else:
            cmd = [sys.executable, str(script_path), config_file.name]

        with log_path.open('a', encoding='utf-8') as log_file:
            log_file.write(f'启动脚本: {script_rel_path}\n命令: {cmd}\n\n')

        process = subprocess.Popen(
            cmd,
            cwd=str(script_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        run = ScriptRun(run_id, process, log_path, config_file.name)
        self.runs[run_id] = run
        self.current_run = run
        threading.Thread(target=self._pipe_output, args=(run,), daemon=True).start()
        return {'ok': True, 'data': {'run_id': run_id}}

    def get_run_status(self, run_id):
        run = self.runs.get(run_id)
        if not run:
            return {'ok': False, 'error': '运行记录不存在'}
        exit_code = run.process.poll()
        if exit_code is not None:
            run.finished = True
            run.exit_code = exit_code
        log = run.log_path.read_text(encoding='utf-8') if run.log_path.exists() else ''
        return {'ok': True, 'data': {'finished': run.finished, 'exit_code': run.exit_code, 'log': log}}

    def stop_current(self):
        if not self.current_run or self.current_run.process.poll() is not None:
            return {'ok': True, 'data': '没有运行中的脚本'}
        self.current_run.process.terminate()
        return {'ok': True, 'data': '已发送停止信号'}

    def _pipe_output(self, run):
        try:
            with run.log_path.open('a', encoding='utf-8') as log_file:
                for line in run.process.stdout:
                    log_file.write(line)
                    log_file.flush()
                exit_code = run.process.wait()
                run.finished = True
                run.exit_code = exit_code
                log_file.write(f'\n脚本结束，退出码: {exit_code}\n')
        finally:
            try:
                os.unlink(run.config_path)
            except OSError:
                pass

    def _safe_script_dir(self, script_rel_path):
        if not script_rel_path:
            return None
        script_dir = (SCRIPTS_DIR / script_rel_path).resolve()
        try:
            script_dir.relative_to(SCRIPTS_DIR.resolve())
        except ValueError:
            return None
        return script_dir

    def _compiled_runner_code(self, script_dir, config_path):
        return f"""
import os, sys
os.chdir({str(script_dir)!r})
sys.path.insert(0, {str(script_dir)!r})
os.environ['SCRIPT_CONFIG_FILE'] = {str(config_path)!r}
import main
if hasattr(main, 'main'):
    try:
        main.main({str(config_path)!r})
    except TypeError:
        main.main()
else:
    print('脚本模块已加载，但未找到 main 函数')
"""


if __name__ == '__main__':
    import webview

    api = Api()
    index_path = WEB_DIR / 'index.html'
    window = webview.create_window('CedarEx 脚本执行器', str(index_path), js_api=api, width=1400, height=1000)
    webview.start(debug=False)
