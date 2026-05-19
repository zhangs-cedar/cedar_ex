import json
import os
import platform
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


class TerminalSession:
    def __init__(self, cwd=None):
        self.cwd = str(cwd or BASE_DIR)
        self.system = platform.system()
        self.output = []
        self.alive = False
        self.lock = threading.Lock()
        self.process = None
        self.master_fd = None
        self.winpty = None

    def start(self, cols=100, rows=30):
        if self.alive:
            return
        if self.system == 'Windows':
            self._start_windows(cols, rows)
        else:
            self._start_posix(cols, rows)
        self.alive = True

    def _start_posix(self, cols, rows):
        import fcntl
        import pty
        import select
        import struct
        import termios

        shell = os.environ.get('SHELL') or ('/bin/zsh' if Path('/bin/zsh').exists() else '/bin/bash')
        master_fd, slave_fd = pty.openpty()
        self.master_fd = master_fd
        self.process = subprocess.Popen(
            [shell],
            cwd=self.cwd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=os.environ.copy(),
            close_fds=True,
        )
        os.close(slave_fd)
        self.resize(cols, rows)

        def reader():
            while self.process and self.process.poll() is None:
                try:
                    ready, _, _ = select.select([master_fd], [], [], 0.1)
                    if ready:
                        data = os.read(master_fd, 4096).decode(errors='ignore')
                        if data:
                            with self.lock:
                                self.output.append(data)
                except OSError:
                    break

        threading.Thread(target=reader, daemon=True).start()

    def _start_windows(self, cols, rows):
        try:
            from winpty import PtyProcess
        except ImportError as exc:
            raise RuntimeError('Windows 真实终端需要安装 pywinpty') from exc

        shell = 'powershell.exe'
        self.winpty = PtyProcess.spawn(shell, cwd=self.cwd, dimensions=(rows, cols))

        def reader():
            while self.winpty and self.winpty.isalive():
                try:
                    data = self.winpty.read(4096)
                    if data:
                        with self.lock:
                            self.output.append(data)
                except Exception:
                    break

        threading.Thread(target=reader, daemon=True).start()

    def read(self):
        with self.lock:
            data = ''.join(self.output)
            self.output.clear()
        return data

    def write(self, data):
        if not self.alive:
            return
        if self.system == 'Windows':
            if self.winpty:
                self.winpty.write(data)
        elif self.master_fd is not None:
            os.write(self.master_fd, data.encode())

    def resize(self, cols, rows):
        if self.system == 'Windows':
            if self.winpty:
                self.winpty.setwinsize(rows, cols)
            return
        if self.master_fd is None:
            return
        import fcntl
        import struct
        import termios

        size = struct.pack('HHHH', rows, cols, 0, 0)
        fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, size)

    def stop(self):
        self.alive = False
        if self.system == 'Windows' and self.winpty:
            try:
                self.winpty.close()
            except Exception:
                pass
        if self.process and self.process.poll() is None:
            self.process.terminate()
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass


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
    def __init__(self, run_id, process, log_path, config_path, script_name, script_rel_path, config):
        self.run_id = run_id
        self.process = process
        self.log_path = log_path
        self.config_path = config_path
        self.script_name = script_name
        self.script_rel_path = script_rel_path
        self.config = config or {}
        self.created_at = datetime.now().isoformat(timespec='seconds')
        self.finished = False
        self.exit_code = None
        self.file_offsets = {}
        self.external_log = []


class Api:
    def __init__(self):
        LOG_DIR.mkdir(exist_ok=True)
        self.runs = {}
        self.current_run = None
        self.window = None
        self.terminal = None

    def set_window(self, window):
        self.window = window

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
        script_dir = self._safe_script_dir(script_rel_path)
        if not script_dir or not has_script_file(script_dir):
            return {'ok': False, 'error': '脚本不存在或不可运行'}

        script_path = get_script_file_path(script_dir)
        config_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
        json.dump(config or {}, config_file, ensure_ascii=False, indent=2)
        config_file.close()

        if str(script_path).endswith(('.so', '.pyd')):
            runner = self._compiled_runner_code(script_dir, config_file.name)
            runner_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py', encoding='utf-8')
            runner_file.write(runner)
            runner_file.close()
            cmd = f'{self._shell_quote(sys.executable)} {self._shell_quote(runner_file.name)}'
        else:
            cmd = f'{self._shell_quote(sys.executable)} {self._shell_quote(str(script_path))} {self._shell_quote(config_file.name)}'

        self.terminal_start()
        terminal_cmd = (
            f'cd {self._shell_quote(str(script_dir))}\n'
            f'export CEDAR_BASE_DIR={self._shell_quote(str(BASE_DIR))}\n'
            f'{cmd}\n'
        )
        self.terminal.write(terminal_cmd)
        return {'ok': True, 'data': {'command': cmd, 'config_file': config_file.name}}

    def get_run_status(self, run_id):
        run = self.runs.get(run_id)
        if not run:
            return {'ok': False, 'error': '运行记录不存在'}
        exit_code = run.process.poll()
        if exit_code is not None:
            run.finished = True
            run.exit_code = exit_code
        self._collect_external_logs(run)
        own_log = run.log_path.read_text(encoding='utf-8') if run.log_path.exists() else ''
        external_log = ''.join(run.external_log)
        log = own_log + ('\n' if own_log and external_log else '') + external_log
        return {'ok': True, 'data': {'finished': run.finished, 'exit_code': run.exit_code, 'log': log}}

    def analyze_run_with_opencode(self, run_id):
        run = self.runs.get(run_id)
        if not run:
            return {'ok': False, 'error': '运行记录不存在'}
        status = self.get_run_status(run_id)
        if not status.get('ok'):
            return status
        log = status['data']['log'] or ''
        prompt = self._build_opencode_review_prompt(run, log)
        try:
            result = subprocess.run(
                ['opencode', 'run', prompt],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=180,
            )
            output = (result.stdout or '') + (result.stderr or '')
            return {'ok': result.returncode == 0, 'error': '' if result.returncode == 0 else f'opencode 退出码: {result.returncode}', 'data': {'review': output, 'exit_code': result.returncode}}
        except FileNotFoundError:
            return {'ok': False, 'error': '未找到 opencode 命令，请先安装或配置 PATH'}
        except subprocess.TimeoutExpired as e:
            output = ((e.stdout or '') if isinstance(e.stdout, str) else '') + ((e.stderr or '') if isinstance(e.stderr, str) else '')
            return {'ok': False, 'error': 'opencode 分析超时', 'data': {'review': output}}

    def _build_opencode_review_prompt(self, run, log):
        max_chars = 24000
        clipped_log = log[-max_chars:]
        clipped_notice = '' if len(log) <= max_chars else f'\n注意：日志较长，以下仅包含最后 {max_chars} 个字符。\n'
        return f"""
你是 CedarEx 本地脚本运行诊断助手。请只分析本次运行结果，不要修改文件，不要执行命令。

请用中文输出，结构如下：
1. 结论：成功 / 失败 / 不确定
2. 关键证据：引用日志中的关键信息
3. 风险与异常：列出错误、告警、可疑点
4. 下一步建议：给出可操作建议

脚本路径：
{run.script_rel_path}

运行时间：
{run.created_at}

退出码：
{run.exit_code}

运行参数：
{json.dumps(run.config, ensure_ascii=False, indent=2)}
{clipped_notice}
运行日志：
```text
{clipped_log}
```
""".strip()

    def stop_current(self):
        if self.terminal:
            self.terminal.write('\x03')
            return {'ok': True, 'data': '已向终端发送 Ctrl+C'}
        return {'ok': True, 'data': '终端未启动'}

    def execute_command(self, command, cwd=None):
        """执行一条本地 shell 命令。

        这是面向单人离线软件的轻量终端能力：支持执行普通命令并返回输出，
        不提供交互式 PTY 会话。
        """
        command = (command or '').strip()
        if not command:
            return {'ok': False, 'error': '命令为空'}

        workdir = BASE_DIR
        if cwd:
            candidate = Path(cwd).expanduser().resolve()
            if candidate.exists() and candidate.is_dir():
                workdir = candidate

        try:
            result = subprocess.run(
                command,
                cwd=str(workdir),
                shell=True,
                executable='/bin/zsh' if Path('/bin/zsh').exists() else None,
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = (result.stdout or '') + (result.stderr or '')
            return {
                'ok': True,
                'data': {
                    'cwd': str(workdir),
                    'command': command,
                    'output': output,
                    'exit_code': result.returncode,
                },
            }
        except subprocess.TimeoutExpired as e:
            output = ((e.stdout or '') if isinstance(e.stdout, str) else '') + ((e.stderr or '') if isinstance(e.stderr, str) else '')
            return {'ok': False, 'error': '命令执行超时，已终止', 'data': {'output': output}}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def terminal_start(self, cols=100, rows=30):
        try:
            if not self.terminal:
                self.terminal = TerminalSession(BASE_DIR)
            self.terminal.start(int(cols or 100), int(rows or 30))
            return {'ok': True, 'data': {'cwd': str(BASE_DIR), 'platform': platform.system()}}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def terminal_read(self):
        if not self.terminal:
            return {'ok': True, 'data': ''}
        return {'ok': True, 'data': self.terminal.read()}

    def terminal_write(self, data):
        if not self.terminal:
            self.terminal_start()
        self.terminal.write(data or '')
        return {'ok': True}

    def terminal_resize(self, cols, rows):
        if self.terminal:
            self.terminal.resize(int(cols or 100), int(rows or 30))
        return {'ok': True}

    def terminal_stop(self):
        if self.terminal:
            self.terminal.stop()
            self.terminal = None
        return {'ok': True}

    def choose_directory(self):
        if not self.window:
            return {'ok': False, 'error': '窗口尚未初始化'}
        import webview

        result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        return {'ok': True, 'data': result[0] if result else ''}

    def choose_file(self):
        if not self.window:
            return {'ok': False, 'error': '窗口尚未初始化'}
        import webview

        result = self.window.create_file_dialog(webview.OPEN_DIALOG)
        return {'ok': True, 'data': result[0] if result else ''}

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

    def _init_log_offsets(self, run):
        """记录已有日志文件大小，后续只读取脚本运行期间新增内容。"""
        if not LOG_DIR.exists():
            return
        for path in LOG_DIR.rglob('*.log'):
            try:
                run.file_offsets[str(path)] = path.stat().st_size
            except OSError:
                run.file_offsets[str(path)] = 0

    def _collect_external_logs(self, run):
        """读取脚本自行写入 log/ 目录的新增内容。

        现有脚本通常通过 cedar.utils.print 写入 LOG_PATH 指向的文件，
        不一定输出到 stdout；因此仅监听 subprocess stdout 会导致运行中无日志。
        """
        if not LOG_DIR.exists():
            return
        for path in sorted(LOG_DIR.rglob('*.log'), key=lambda p: str(p)):
            if path.resolve() == run.log_path.resolve():
                continue
            key = str(path)
            try:
                last_offset = run.file_offsets.get(key, 0)
                size = path.stat().st_size
                if size < last_offset:
                    last_offset = 0
                if size == last_offset:
                    continue
                with path.open('r', encoding='utf-8') as f:
                    f.seek(last_offset)
                    content = f.read()
                run.file_offsets[key] = size
                if content:
                    rel_path = path.relative_to(LOG_DIR)
                    run.external_log.append(f'\n--- {rel_path} ---\n{content}')
            except (OSError, UnicodeDecodeError):
                continue

    def _safe_script_dir(self, script_rel_path):
        if not script_rel_path:
            return None
        script_dir = (SCRIPTS_DIR / script_rel_path).resolve()
        try:
            script_dir.relative_to(SCRIPTS_DIR.resolve())
        except ValueError:
            return None
        return script_dir

    def _shell_quote(self, value):
        import shlex

        return shlex.quote(str(value))

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
    api.set_window(window)
    webview.start(debug=False)
