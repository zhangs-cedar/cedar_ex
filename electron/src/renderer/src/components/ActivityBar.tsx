import type { ViewKey } from '../App'

const views: { key: ViewKey; icon: string; title: string }[] = [
  { key: 'explorer', icon: '📁', title: '脚本资源管理器' },
  { key: 'search', icon: '⌕', title: '搜索脚本' },
  { key: 'run', icon: '▶', title: '运行脚本' },
  { key: 'history', icon: '⑂', title: '运行历史' },
  { key: 'ai', icon: 'AI', title: 'AI 助手' },
]

export function ActivityBar({ activeView, onViewChange }: { activeView: ViewKey; onViewChange: (v: ViewKey) => void }) {
  return (
    <nav className='activity-bar' aria-label='主功能'>
      {views.map(({ key, icon, title }) => (
        <button
          key={key}
          className={`activity-item ${key === 'ai' ? 'ai' : ''} ${activeView === key ? 'active' : ''}`}
          title={title}
          onClick={() => onViewChange(key)}
        >
          {icon}
        </button>
      ))}
    </nav>
  )
}
