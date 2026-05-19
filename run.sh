#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELECTRON_DIR="$ROOT_DIR/electron"

if ! command -v node >/dev/null 2>&1; then
  printf 'Error: node is not installed or not in PATH.\n' >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  printf 'Error: npm is not installed or not in PATH.\n' >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  printf 'Error: python3 is not installed or not in PATH.\n' >&2
  exit 1
fi

if [ ! -d "$ELECTRON_DIR/node_modules" ]; then
  printf 'Installing Electron dependencies...\n'
  npm install --prefix "$ELECTRON_DIR"
fi

printf 'Starting CedarEx Electron app...\n'
cd "$ELECTRON_DIR"
exec npm run dev
