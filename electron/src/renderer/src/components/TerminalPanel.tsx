import { useRef, useEffect, useState, useCallback } from 'react'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'

interface Props {
  onTranscriptChange: (text: string) => void
  onAnalyze: () => void
  showToast: (msg: string) => void
}

export function TerminalPanel({ onTranscriptChange, onAnalyze, showToast }: Props) {
  const terminalRef = useRef<HTMLDivElement>(null)
  const xtermRef = useRef<Terminal | null>(null)
  const fitAddonRef = useRef<FitAddon | null>(null)
  const pollerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [title, setTitle] = useState('空闲')

  const initTerminal = useCallback(async () => {
    if (!terminalRef.current || xtermRef.current) return

    const term = new Terminal({
      cursorBlink: true,
      convertEol: true,
      fontSize: 13,
      fontFamily: "'SF Mono', Monaco, 'Fira Code', 'Droid Sans Mono', monospace",
      theme: {
        background: '#050816',
        foreground: '#d1d5db',
        cursor: '#22c55e',
        selectionBackground: '#2563eb66',
      },
    })

    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(terminalRef.current)
    fitAddon.fit()

    xtermRef.current = term
    fitAddonRef.current = fitAddon

    // 启动 Python sidecar 终端
    const cols = term.cols || 100
    const rows = term.rows || 30
    const started = await window.cedar.terminalStart(cols, rows)
    if (!started.ok) {
      term.writeln(`终端启动失败: ${started.error}`)
      return
    }
    setTitle(`真实终端 — ${(started.data as { platform?: string })?.platform || 'ready'}`)

    // 终端输入 → Python
    term.onData((data) => {
      window.cedar.terminalWrite(data)
    })

    // 终输出轮询 → xterm
    let transcript = ''
    pollerRef.current = setInterval(async () => {
      const res = await window.cedar.terminalRead()
      if (res.ok && res.data) {
        transcript += res.data
        term.write(res.data)
      }
    }, 50)

    // 定期更新 transcript
    const transcriptTimer = setInterval(() => {
      if (transcript) {
        onTranscriptChange(transcript)
        transcript = ''
      }
    }, 500)

    // 自适应
    const resizeHandler = () => {
      fitAddon.fit()
      const c = term.cols || 100
      const r = term.rows || 30
      window.cedar.terminalResize(c, r)
    }
    window.addEventListener('resize', resizeHandler)

    // Cleanup function stored on ref
    const cleanup = () => {
      clearInterval(pollerRef.current!)
      clearInterval(transcriptTimer)
      window.removeEventListener('resize', resizeHandler)
    }
    ;(term as any).__cleanup = cleanup
  }, [onTranscriptChange])

  useEffect(() => {
    initTerminal()
    return () => {
      if (pollerRef.current) clearInterval(pollerRef.current)
      if (xtermRef.current) {
        ;(xtermRef.current as any).__cleanup?.()
        xtermRef.current.dispose()
      }
    }
  }, [initTerminal])

  const restartTerminal = useCallback(async () => {
    await window.cedar.terminalStop()
    if (pollerRef.current) clearInterval(pollerRef.current)
    xtermRef.current?.dispose()
    xtermRef.current = null
    setTitle('空闲')
    initTerminal()
    showToast('已新建终端')
  }, [initTerminal, showToast])

  const clearLog = useCallback(() => {
    xtermRef.current?.clear()
    showToast('终端已清屏')
  }, [showToast])

  const copyLog = useCallback(async () => {
    try {
      // Use xterm selection
      const selection = xtermRef.current?.getSelection()
      if (selection) {
        await navigator.clipboard.writeText(selection)
        showToast('已复制选中内容')
      } else {
        showToast('没有选中内容，拖动鼠标选择后复制')
      }
    } catch {
      showToast('复制失败')
    }
  }, [showToast])

  return (
    <section className='terminal-panel'>
      <div className='panel-tabs'>
        <b>终端</b>
        <span>问题</span>
        <span>输出</span>
        <span>AI 分析</span>
        <div className='terminal-actions'>
          <button onClick={restartTerminal}>新建终端</button>
          <button onClick={onAnalyze}>AI 分析</button>
          <button onClick={copyLog}>复制</button>
          <button onClick={clearLog}>清空</button>
        </div>
      </div>
      <div className='terminal-window'>
        <div className='terminal-titlebar'>
          <div className='traffic-lights' style={{ display: 'flex', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', display: 'block', background: '#ff5f57' }}></span>
            <span style={{ width: 10, height: 10, borderRadius: '50%', display: 'block', background: '#ffbd2e' }}></span>
            <span style={{ width: 10, height: 10, borderRadius: '50%', display: 'block', background: '#28c840' }}></span>
          </div>
          <div className='terminal-title'>cedarex — {title}</div>
          <div className='terminal-badge'>真实终端</div>
        </div>
        <div ref={terminalRef} className='xterm-host' />
      </div>
    </section>
  )
}
