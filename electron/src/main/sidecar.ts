import { ChildProcess, spawn } from 'child_process'
import { join } from 'path'
import { createInterface } from 'readline'
import { app } from 'electron'
import * as fs from 'fs'

/**
 * Python sidecar 管理器
 * 通过 stdin/stdout JSON-RPC 与 Python 后端通信
 */
export class Sidecar {
  private process: ChildProcess | null = null
  private requestId = 0
  private pending = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>()
  private ready = false

  get isRunning(): boolean {
    return this.process !== null && this.ready
  }

  async start(): Promise<void> {
    const pythonPath = process.platform === 'win32' ? 'python' : 'python3'

    // 查找 sidecar.py
    const searchPaths = [
      // 开发模式
      join(app.getAppPath(), '..', 'sidecar.py'),
      join(app.getAppPath(), 'sidecar.py'),
      // 打包后 extraResources
      join(process.resourcesPath, 'sidecar.py'),
      // 当前目录
      join(process.cwd(), 'sidecar.py'),
      // 项目根目录
      join(__dirname, '..', '..', '..', 'sidecar.py'),
      join(__dirname, '..', '..', '..', '..', 'sidecar.py'),
    ]

    let foundPath = ''
    for (const p of searchPaths) {
      try {
        if (fs.existsSync(p)) {
          foundPath = p
          break
        }
      } catch {
        continue
      }
    }

    if (!foundPath) {
      console.warn('[Sidecar] sidecar.py not found, running in demo mode')
      this.ready = true
      return
    }

    console.log(`[Sidecar] Starting: ${pythonPath} ${foundPath}`)

    return new Promise<void>((resolve) => {
      this.process = spawn(pythonPath, [foundPath, '--stdio'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
      })

      let started = false

      const rl = createInterface({ input: this.process!.stdout! })
      rl.on('line', (line: string) => {
        try {
          const msg = JSON.parse(line)
          if (msg.method === 'ready') {
            this.ready = true
            if (!started) {
              started = true
              resolve()
            }
            return
          }
          this.handleMessage(msg)
        } catch {
          console.log('[Sidecar]', line)
        }
      })

      this.process.stderr?.on('data', (data: Buffer) => {
        console.error('[Sidecar:err]', data.toString())
      })

      this.process.on('exit', (code) => {
        console.log(`[Sidecar] exited with code ${code}`)
        this.ready = false
        this.process = null
        for (const [id, p] of this.pending) {
          p.reject(new Error(`Sidecar exited with code ${code}`))
          this.pending.delete(id)
        }
      })

      // 超时后备
      setTimeout(() => {
        if (!started) {
          this.ready = true
          started = true
          resolve()
        }
      }, 3000)
    })
  }

  private handleMessage(msg: { id?: number; ok?: boolean; data?: unknown; error?: string }): void {
    if (msg.id !== undefined && this.pending.has(msg.id)) {
      const p = this.pending.get(msg.id)!
      this.pending.delete(msg.id)
      p.resolve({ ok: msg.ok ?? !msg.error, data: msg.data, error: msg.error })
    }
  }

  async call(method: string, ...args: unknown[]): Promise<unknown> {
    if (!this.ready || !this.process?.stdin) {
      return { ok: false, error: 'Sidecar 未就绪' }
    }

    const id = ++this.requestId
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject })
      const msg = JSON.stringify({ id, method, args }) + '\n'
      this.process!.stdin!.write(msg)
      // 30 秒超时
      setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id)
          resolve({ ok: false, error: '请求超时' })
        }
      }, 30000)
    })
  }

  stop(): void {
    if (this.process) {
      try {
        this.process.stdin?.end()
        this.process.kill('SIGTERM')
        setTimeout(() => {
          try { this.process?.kill('SIGKILL') } catch { /* ignore */ }
        }, 2000)
      } catch {
        // ignore
      }
      this.process = null
    }
    this.ready = false
  }
}
