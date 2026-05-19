import { useState, useEffect } from 'react'
import type { ViewKey } from '../App'
import type { ScriptNode, LogItem } from '../types/api'
import { ScriptTree } from './ScriptTree'
import { SidePanel } from './SidePanel'

const titles: Record<string, string> = {
  explorer: '脚本资源管理器',
  run: '运行脚本',
  search: '搜索脚本',
  history: '运行历史',
  ai: 'AI 助手',
}

interface Props {
  scripts: ScriptNode[]
  activeView: ViewKey
  selectedPath: string | null
  searchQuery: string
  onSearchChange: (q: string) => void
  onSelectScript: (node: ScriptNode) => void
  onRefresh: () => void
  scriptCount: number
  showToast: (msg: string) => void
}

export function Sidebar({ scripts, activeView, selectedPath, searchQuery, onSearchChange, onSelectScript, onRefresh, scriptCount, showToast }: Props) {
  const [logs, setLogs] = useState<LogItem[]>([])

  useEffect(() => {
    if (activeView === 'history') {
      window.cedar.getRecentLogs(20).then(res => {
        if (res.ok && res.data) setLogs(res.data)
      })
    }
  }, [activeView])

  const showTree = activeView === 'explorer' || activeView === 'search'
  const showPanel = !showTree

  return (
    <aside className='sidebar'>
      <div className='side-title'>{titles[activeView] || '脚本资源管理器'}</div>

      {showTree && (
        <>
          <label className='search-box'>
            <span>⌕</span>
            <input
              placeholder='搜索 scripts...'
              value={searchQuery}
              onChange={e => onSearchChange(e.target.value)}
              autoFocus={activeView === 'search'}
            />
          </label>
          <div className='sidebar-meta'>
            <span>{scriptCount} 个脚本</span>
            <button onClick={onRefresh}>刷新</button>
          </div>
          <ScriptTree
            scripts={scripts}
            selectedPath={selectedPath}
            searchQuery={searchQuery}
            onSelect={onSelectScript}
          />
        </>
      )}

      {showPanel && (
        <SidePanel
          view={activeView}
          logs={logs}
          showToast={showToast}
        />
      )}
    </aside>
  )
}
