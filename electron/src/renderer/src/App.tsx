import { useState, useEffect, useCallback } from 'react'
import { ActivityBar } from './components/ActivityBar'
import { Sidebar } from './components/Sidebar'
import { EditorTabs } from './components/EditorTabs'
import { EditorArea } from './components/EditorArea'
import { TerminalPanel } from './components/TerminalPanel'
import { StatusBar } from './components/StatusBar'
import { Toast } from './components/Toast'
import type { ScriptNode, ScriptDetail } from './types/api'

export type ViewKey = 'explorer' | 'run' | 'search' | 'history' | 'ai'
export type EditorTab = 'form' | 'readme' | 'history'

function App() {
  const [scripts, setScripts] = useState<ScriptNode[]>([])
  const [activeView, setActiveView] = useState<ViewKey>('explorer')
  const [activeEditorTab, setActiveEditorTab] = useState<EditorTab>('form')
  const [selectedPath, setSelectedPath] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<ScriptNode | null>(null)
  const [scriptDetail, setScriptDetail] = useState<ScriptDetail | null>(null)
  const [running, setRunning] = useState(false)
  const [terminalTranscript, setTerminalTranscript] = useState('')
  const [toast, setToast] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const showToast = useCallback((msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2600)
  }, [])

  // 加载脚本
  const loadScripts = useCallback(async () => {
    const res = await window.cedar.getScripts()
    if (res.ok && res.data) {
      setScripts(res.data)
    } else {
      showToast(res.error || '加载脚本失败')
    }
  }, [showToast])

  useEffect(() => {
    loadScripts()
  }, [loadScripts])

  // 选择脚本
  const selectScript = useCallback(async (node: ScriptNode) => {
    if (running) {
      showToast('脚本运行中，请结束后再切换')
      return
    }
    setSelectedPath(node.path)
    setSelectedNode(node)
    setActiveEditorTab('form')
    const res = await window.cedar.getScriptDetail(node.path)
    if (res.ok && res.data) {
      setScriptDetail(res.data)
    } else {
      showToast(res.error || '读取脚本详情失败')
    }
  }, [running, showToast])

  // 运行脚本
  const runScript = useCallback(async (config: Record<string, unknown>) => {
    if (!selectedPath || running) return
    setRunning(true)
    try {
      const res = await window.cedar.runScript(selectedPath, config)
      if (!res.ok) {
        showToast(res.error || '启动失败')
      } else {
        showToast('已发送到终端')
      }
    } catch (e) {
      showToast(String(e))
    } finally {
      setRunning(false)
    }
  }, [selectedPath, running, showToast])

  const scriptCount = scripts.reduce((count, node) => count + countRunnable(node), 0)

  return (
    <div className='vscode-shell'>
      <header className='titlebar'>
        <div className='window-dots'><span></span><span></span><span></span></div>
        <div className='command-center'>CedarEx：搜索脚本、输入命令或询问 AI</div>
        <div className='title-meta'>Python · 本地工作区</div>
      </header>

      <div className='main-layout'>
        <ActivityBar activeView={activeView} onViewChange={setActiveView} />

        <Sidebar
          scripts={scripts}
          activeView={activeView}
          selectedPath={selectedPath}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onSelectScript={selectScript}
          onRefresh={loadScripts}
          scriptCount={scriptCount}
          showToast={showToast}
        />

        <main className='workspace'>
          <EditorTabs
            activeTab={activeEditorTab}
            onTabChange={setActiveEditorTab}
            scriptName={selectedNode?.name ?? '选择一个脚本开始'}
          />

          <EditorArea
            activeTab={activeEditorTab}
            selectedPath={selectedPath}
            selectedNode={selectedNode}
            scriptDetail={scriptDetail}
            running={running}
            onRun={runScript}
            onStop={() => window.cedar.stopCurrent()}
            onReset={() => {
              if (selectedPath) {
                window.cedar.getScriptDetail(selectedPath).then(res => {
                  if (res.ok && res.data) setScriptDetail({ ...res.data })
                })
              }
            }}
            onAnalyze={(log) => {
              if (!selectedNode || !scriptDetail) return
              window.cedar
                .analyzeTerminal(selectedPath, collectConfigFromForm(), log)
                .then(res => {
                  if (res.ok && res.data) {
                    showToast('AI 分析完成')
                  }
                })
            }}
            terminalTranscript={terminalTranscript}
            showToast={showToast}
          />

          <TerminalPanel
            onTranscriptChange={setTerminalTranscript}
            onAnalyze={() => {
              if (!selectedNode || !scriptDetail) return
              window.cedar
                .analyzeTerminal(selectedPath, collectConfigFromForm(), terminalTranscript)
                .then(() => showToast('AI 分析已触发'))
            }}
            showToast={showToast}
          />
        </main>
      </div>

      <StatusBar running={running} />
      <Toast message={toast} />
    </div>
  )
}

function countRunnable(node: ScriptNode): number {
  return (node.runnable ? 1 : 0) + (node.children?.reduce((sum, c) => sum + countRunnable(c), 0) ?? 0)
}

function collectConfigFromForm(): Record<string, unknown> {
  const config: Record<string, unknown> = {}
  document.querySelectorAll('[data-name]').forEach(el => {
    const name = (el as HTMLElement).dataset.name
    if (!name) return
    const input = el as HTMLInputElement
    const type = (el as HTMLElement).dataset.type
    if (type === 'bool') config[name] = input.checked
    else if (type === 'int') config[name] = input.value === '' ? null : parseInt(input.value, 10)
    else if (type === 'float') config[name] = input.value === '' ? null : Number(input.value)
    else config[name] = input.value
  })
  return config
}

export default App
