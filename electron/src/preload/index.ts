import { contextBridge, ipcRenderer } from 'electron'

const api = {
  getScripts: () => ipcRenderer.invoke('sidecar:getScripts'),
  getScriptDetail: (path: string) => ipcRenderer.invoke('sidecar:getScriptDetail', path),
  runScript: (path: string, config: unknown) => ipcRenderer.invoke('sidecar:runScript', path, config),

  terminalStart: (cols?: number, rows?: number) => ipcRenderer.invoke('sidecar:terminalStart', cols, rows),
  terminalRead: () => ipcRenderer.invoke('sidecar:terminalRead'),
  terminalWrite: (data: string) => ipcRenderer.invoke('sidecar:terminalWrite', data),
  terminalResize: (cols: number, rows: number) => ipcRenderer.invoke('sidecar:terminalResize', cols, rows),
  terminalStop: () => ipcRenderer.invoke('sidecar:terminalStop'),

  stopCurrent: () => ipcRenderer.invoke('sidecar:stopCurrent'),
  analyzeRun: (runId: string) => ipcRenderer.invoke('sidecar:analyzeRun', runId),
  analyzeTerminal: (path: string, config: unknown, log: string) =>
    ipcRenderer.invoke('sidecar:analyzeTerminal', path, config, log),
  aiAssist: (payload: unknown) => ipcRenderer.invoke('sidecar:aiAssist', payload),

  getRecentLogs: (limit?: number) => ipcRenderer.invoke('sidecar:getRecentLogs', limit),
  getLogDetail: (path: string, maxChars?: number) => ipcRenderer.invoke('sidecar:getLogDetail', path, maxChars),

  chooseDirectory: () => ipcRenderer.invoke('sidecar:chooseDirectory'),
  chooseFile: () => ipcRenderer.invoke('sidecar:chooseFile')
}

contextBridge.exposeInMainWorld('cedar', api)
