#!/usr/bin/env python3
"""
CedarEx Sidecar — JSON-RPC over stdio
Electron 主进程通过 stdin/stdout 与本进程通信

用法：
    python3 sidecar.py --stdio

支持的方法：get_scripts, get_script_detail, run_script,
terminal_start, terminal_read, terminal_write, terminal_resize, terminal_stop,
stop_current, analyze_run_with_opencode, analyze_terminal_with_opencode, ai_assist,
get_recent_logs, get_log_detail
"""

import json
import os
import sys
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(str(BASE_DIR))

from main_webview import Api, TerminalSession


class SidecarApi:
    """包装 Api 类，移除 pywebview 依赖，适配 stdio JSON-RPC"""

    def __init__(self):
        self._api = Api()
        self._api.terminal = None  # 终端由我们直接管理
        self._terminal = None      # 独立 TerminalSession 实例

    def _dispatch(self, method: str, args: list) -> dict:
        """先查自己（重写的方法），再查原始 Api"""
        fn = getattr(self, method, None)
        if fn is None:
            fn = getattr(self._api, method, None)
        if fn is None:
            return {'ok': False, 'error': f'未知方法: {method}'}
        try:
            result = fn(*args)
            return result if isinstance(result, dict) else {'ok': True, 'data': result}
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            return {'ok': False, 'error': str(e)}

    # ── 文件选择 —— Electron 侧处理 ──
    def choose_directory(self):
        return {'ok': False, 'error': '请在 Electron 中使用原生对话框'}
    def choose_file(self):
        return {'ok': False, 'error': '请在 Electron 中使用原生对话框'}

    # ── 终端管理 ──
    def terminal_start(self, cols=100, rows=30):
        try:
            if not self._terminal:
                self._terminal = TerminalSession(BASE_DIR)
                self._api.terminal = self._terminal
            self._terminal.start(int(cols or 100), int(rows or 30))
            import platform
            return {'ok': True, 'data': {'cwd': str(BASE_DIR), 'platform': platform.system()}}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def run_script(self, script_rel_path, config):
        """通过共享 PTY 运行脚本，确保 Electron 终端能读到输出。"""
        started = self.terminal_start()
        if not started.get('ok'):
            return started
        self._api.terminal = self._terminal
        return self._api.run_script(script_rel_path, config)

    def terminal_read(self):
        if not self._terminal:
            return {'ok': True, 'data': ''}
        return {'ok': True, 'data': self._terminal.read()}

    def terminal_write(self, data):
        if not self._terminal:
            self.terminal_start()
        self._terminal.write(data or '')
        return {'ok': True}

    def terminal_resize(self, cols, rows):
        if self._terminal:
            self._terminal.resize(int(cols or 100), int(rows or 30))
        return {'ok': True}

    def terminal_stop(self):
        if self._terminal:
            self._terminal.stop()
            self._terminal = None
            self._api.terminal = None
        return {'ok': True}

    def stop_current(self):
        """向终端发送 Ctrl+C"""
        if self._terminal:
            self._terminal.write('\x03')
            return {'ok': True, 'data': '已向终端发送 Ctrl+C'}
        return {'ok': True, 'data': '终端未启动'}


def main():
    sidecar = SidecarApi()

    # 发送 ready 信号
    sys.stdout.write(json.dumps({'method': 'ready'}) + '\n')
    sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            msg_id = msg.get('id')
            method = msg.get('method', '')
            args = msg.get('args', [])

            result = sidecar._dispatch(method, args)

            response = {'id': msg_id, **result}
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + '\n')
            sys.stdout.flush()
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({'ok': False, 'error': 'JSON 解析失败'}) + '\n')
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(json.dumps({'ok': False, 'error': str(e)}) + '\n')
            sys.stdout.flush()


if __name__ == '__main__':
    main()
