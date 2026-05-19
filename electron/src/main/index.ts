import { app, BrowserWindow, ipcMain, shell, dialog } from 'electron'
import { join } from 'path'
import { Sidecar } from './sidecar'

const isDev = !app.isPackaged

let mainWindow: BrowserWindow | null = null
let sidecar: Sidecar | null = null

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 960,
    minHeight: 640,
    title: 'CedarEx',
    show: false,
    frame: true,
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (isDev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(async () => {
  // 启动 Python sidecar
  sidecar = new Sidecar()
  await sidecar.start()

  // 注册 IPC 处理
  registerIpcHandlers()

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  sidecar?.stop()
  if (process.platform !== 'darwin') app.quit()
})

function registerIpcHandlers(): void {
  const api = async (method: string, ...args: unknown[]) => {
    if (!sidecar) return { ok: false, error: 'Sidecar 未启动' }
    try {
      return await sidecar.call(method, ...args)
    } catch (error) {
      return { ok: false, error: error instanceof Error ? error.message : String(error) }
    }
  }

  ipcMain.handle('sidecar:getScripts', () => api('get_scripts'))
  ipcMain.handle('sidecar:getScriptDetail', (_e, path: string) => api('get_script_detail', path))
  ipcMain.handle('sidecar:runScript', (_e, path: string, config: unknown) => api('run_script', path, config))

  ipcMain.handle('sidecar:terminalStart', (_e, cols?: number, rows?: number) => api('terminal_start', cols ?? 100, rows ?? 30))
  ipcMain.handle('sidecar:terminalRead', () => api('terminal_read'))
  ipcMain.handle('sidecar:terminalWrite', (_e, data: string) => api('terminal_write', data))
  ipcMain.handle('sidecar:terminalResize', (_e, cols: number, rows: number) => api('terminal_resize', cols, rows))
  ipcMain.handle('sidecar:terminalStop', () => api('terminal_stop'))

  ipcMain.handle('sidecar:stopCurrent', () => api('stop_current'))
  ipcMain.handle('sidecar:analyzeRun', (_e, runId: string) => api('analyze_run_with_opencode', runId))
  ipcMain.handle('sidecar:analyzeTerminal', (_e, path: string, config: unknown, log: string) =>
    api('analyze_terminal_with_opencode', path, config, log)
  )
  ipcMain.handle('sidecar:aiAssist', (_e, payload: unknown) => api('ai_assist', payload))
  ipcMain.handle('sidecar:getRecentLogs', (_e, limit?: number) => api('get_recent_logs', limit ?? 20))
  ipcMain.handle('sidecar:getLogDetail', (_e, path: string, maxChars?: number) =>
    api('get_log_detail', path, maxChars ?? 120000)
  )

  // 文件选择 — 使用 Electron 原生对话框
  ipcMain.handle('sidecar:chooseDirectory', async () => {
    const result = await dialog.showOpenDialog(mainWindow!, { properties: ['openDirectory'] })
    return { ok: true, data: result.filePaths[0] || '' }
  })
  ipcMain.handle('sidecar:chooseFile', async () => {
    const result = await dialog.showOpenDialog(mainWindow!, { properties: ['openFile'] })
    return { ok: true, data: result.filePaths[0] || '' }
  })
}
