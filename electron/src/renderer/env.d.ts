/// <reference types="vite/client" />

interface Window {
  cedar: {
    getScripts: () => Promise<{ ok: boolean; data?: unknown; error?: string }>
    getScriptDetail: (path: string) => Promise<{ ok: boolean; data?: unknown; error?: string }>
    runScript: (path: string, config: unknown) => Promise<{ ok: boolean; data?: unknown; error?: string }>
    terminalStart: (cols?: number, rows?: number) => Promise<{ ok: boolean; data?: unknown; error?: string }>
    terminalRead: () => Promise<{ ok: boolean; data?: string; error?: string }>
    terminalWrite: (data: string) => Promise<{ ok: boolean; error?: string }>
    terminalResize: (cols: number, rows: number) => Promise<{ ok: boolean; error?: string }>
    terminalStop: () => Promise<{ ok: boolean; error?: string }>
    stopCurrent: () => Promise<{ ok: boolean; data?: unknown; error?: string }>
    analyzeRun: (runId: string) => Promise<{ ok: boolean; data?: { review: string }; error?: string }>
    analyzeTerminal: (path: string, config: unknown, log: string) => Promise<{ ok: boolean; data?: { review: string }; error?: string }>
    aiAssist: (payload: unknown) => Promise<{ ok: boolean; data?: { review: string }; error?: string }>
    getRecentLogs: (limit?: number) => Promise<{ ok: boolean; data?: unknown[]; error?: string }>
    getLogDetail: (path: string, maxChars?: number) => Promise<{ ok: boolean; data?: unknown; error?: string }>
    chooseDirectory: () => Promise<{ ok: boolean; data?: string; error?: string }>
    chooseFile: () => Promise<{ ok: boolean; data?: string; error?: string }>
    mermaid?: typeof import('mermaid')
  }
}

declare module 'xterm-addon-fit'
