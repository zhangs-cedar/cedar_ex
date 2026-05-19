import type { ViewKey } from '../App'
import type { LogItem } from '../types/api'

interface Props {
  view: ViewKey
  logs: LogItem[]
  showToast: (msg: string) => void
}

export function SidePanel({ view, logs, showToast }: Props) {
  if (view === 'run') {
    return (
      <div className='side-panel'>
        <div className='side-card'>
          <b>当前脚本</b>
          <p>在 Explorer 中选择一个脚本后，在此处运行和停止。</p>
        </div>
        <div className='side-card'>
          <b>终端</b>
          <p>底部面板为真实 PTY 终端，支持交互命令输入。</p>
        </div>
      </div>
    )
  }

  if (view === 'ai') {
    return (
      <div className='side-panel'>
        <div className='side-card'>
          <b>AI 助手</b>
          <p>右侧面板提供参数解释、日志诊断、命令生成等快捷 AI 操作。</p>
        </div>
        <div className='side-card'>
          <b>建议</b>
          <p>先运行脚本，再调用 AI 分析，可以看到完整输出和错误信息。</p>
        </div>
      </div>
    )
  }

  if (view === 'history') {
    return (
      <div className='side-panel'>
        {logs.length === 0 && <div className='side-card'><p>暂无历史日志。</p></div>}
        {logs.map(item => (
          <button
            key={item.path}
            className='history-item'
            onClick={() => {
              window.cedar.getLogDetail(item.path).then(res => {
                if (res.ok && res.data) {
                  // 在 AI Review 面板显示
                  window.dispatchEvent(new CustomEvent('show-log-detail', { detail: res.data }))
                }
              })
            }}
          >
            {item.path}
            <small>{item.modified} · {Math.round(item.size / 1024)} KB</small>
          </button>
        ))}
      </div>
    )
  }

  return null
}
