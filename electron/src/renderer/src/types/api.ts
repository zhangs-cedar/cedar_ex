export interface ScriptNode {
  name: string
  path: string
  runnable: boolean
  children: ScriptNode[]
}

export interface ScriptField {
  name: string
  label?: string
  type: string
  default?: unknown
  required?: boolean
  description?: string
  options?: string[]
  min?: number
  max?: number
}

export interface ScriptDetail {
  path: string
  fields: ScriptField[]
  doc: string
}

export interface LogItem {
  name: string
  path: string
  modified: string
  size: number
  preview: string
}

export interface LogDetail {
  name: string
  path: string
  modified: string
  size: number
  content: string
  clipped: boolean
}

export interface ApiResult<T = unknown> {
  ok: boolean
  data?: T
  error?: string
}

export interface AiAssistPayload {
  action: string
  script_path: string | null
  script_name: string
  fields: ScriptField[]
  config: Record<string, unknown>
  doc: string
  terminal_log: string
}

declare global {
  interface Window {
    cedar: {
      getScripts: () => Promise<ApiResult<ScriptNode[]>>
      getScriptDetail: (path: string) => Promise<ApiResult<ScriptDetail>>
      runScript: (path: string, config: unknown) => Promise<ApiResult>

      terminalStart: (cols?: number, rows?: number) => Promise<ApiResult>
      terminalRead: () => Promise<ApiResult<string>>
      terminalWrite: (data: string) => Promise<ApiResult>
      terminalResize: (cols: number, rows: number) => Promise<ApiResult>
      terminalStop: () => Promise<ApiResult>

      stopCurrent: () => Promise<ApiResult>
      analyzeRun: (runId: string) => Promise<ApiResult<{ review: string }>>
      analyzeTerminal: (path: string, config: unknown, log: string) => Promise<ApiResult<{ review: string }>>
      aiAssist: (payload: AiAssistPayload) => Promise<ApiResult<{ review: string }>>

      getRecentLogs: (limit?: number) => Promise<ApiResult<LogItem[]>>
      getLogDetail: (path: string, maxChars?: number) => Promise<ApiResult<LogDetail>>

      chooseDirectory: () => Promise<ApiResult<string>>
      chooseFile: () => Promise<ApiResult<string>>
    }
  }
}
