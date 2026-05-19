import type { EditorTab } from '../App'

interface Props {
  activeTab: EditorTab
  onTabChange: (tab: EditorTab) => void
  scriptName: string
}

export function EditorTabs({ activeTab, onTabChange, scriptName }: Props) {
  const tabs: { key: EditorTab; label: string }[] = [
    { key: 'form', label: scriptName },
    { key: 'readme', label: 'README.md 预览' },
    { key: 'history', label: '运行历史' },
  ]

  return (
    <div className='tabs'>
      {tabs.map(tab => (
        <button
          key={tab.key}
          className={`tab ${activeTab === tab.key ? 'active' : ''}`}
          onClick={() => onTabChange(tab.key)}
        >
          {tab.key === 'form' ? scriptName : tab.label}
        </button>
      ))}
    </div>
  )
}
