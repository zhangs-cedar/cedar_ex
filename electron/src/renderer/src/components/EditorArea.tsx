import { useRef, useState, useEffect } from 'react'
import type { EditorTab } from '../App'
import type { ScriptNode, ScriptDetail } from '../types/api'
import { ConfigForm } from './ConfigForm'
import { ReadmePreview } from './ReadmePreview'
import { AiPanel } from './AiPanel'
import { AiReview } from './AiReview'
import { MonacoEditor } from './MonacoEditor'

interface Props {
  activeTab: EditorTab
  selectedPath: string | null
  selectedNode: ScriptNode | null
  scriptDetail: ScriptDetail | null
  running: boolean
  onRun: (config: Record<string, unknown>) => void
  onStop: () => void
  onReset: () => void
  onAnalyze: (log: string) => void
  terminalTranscript: string
  showToast: (msg: string) => void
}

export function EditorArea({
  activeTab,
  selectedPath,
  selectedNode,
  scriptDetail,
  running,
  onRun,
  onStop,
  onReset,
  onAnalyze,
  terminalTranscript,
  showToast,
}: Props) {
  const [aiReviewContent, setAiReviewContent] = useState<string | null>(null)
  const [status, setStatus] = useState<string>('空闲')

  // 监听历史日志详情事件
  useEffect(() => {
    const handler = (e: CustomEvent) => {
      const data = e.detail
      if (data?.content) {
        const clipped = data.clipped ? '\n\n> 日志较长，仅展示最后一部分。' : ''
        setAiReviewContent(
          `### 运行详情：${data.path}\n\n- 修改时间：${data.modified}\n- 文件大小：${Math.round(data.size / 1024)} KB${clipped}\n\n\`\`\`text\n${data.content}\n\`\`\``
        )
      }
    }
    window.addEventListener('show-log-detail', handler as EventListener)
    return () => window.removeEventListener('show-log-detail', handler as EventListener)
  }, [])

  return (
    <section className='editor-area'>
      <div className='editor-pane'>
        {/* Form 视图 */}
        {activeTab === 'form' && (
          <>
            {!selectedPath && (
              <div className='empty-state'>
                <div className='empty-icon'>▶</div>
                <h3>选择脚本，填写参数，然后运行</h3>
                <p>底部是真实终端，可直接输入命令，也会承接脚本执行输出。</p>
              </div>
            )}
            {selectedPath && scriptDetail && (
              <>
                <div className='topbar'>
                  <div>
                    <div className='eyebrow'>当前任务</div>
                    <p className='muted'>{selectedPath}</p>
                  </div>
                  <div className={`run-state ${status === '运行中' ? 'running' : ''}`}>
                    {status}
                  </div>
                </div>
                <ConfigForm
                  fields={scriptDetail.fields}
                  onRun={onRun}
                  onStop={onStop}
                  onReset={onReset}
                  running={running}
                  selectedPath={selectedPath}
                />
              </>
            )}
          </>
        )}

        {/* README 视图 */}
        {activeTab === 'readme' && (
          <ReadmePreview doc={scriptDetail?.doc ?? ''} />
        )}

        {/* 历史视图 */}
        {activeTab === 'history' && (
          <div className='empty-state'>
            <div className='empty-icon'>⑂</div>
            <h3>运行历史</h3>
            <p>左侧侧栏显示最近 20 条历史日志，点击可查看详情。</p>
          </div>
        )}

        {/* 日志详情/AI Review 显示区 */}
        <AiReview
          content={aiReviewContent}
          onClose={() => setAiReviewContent(null)}
        />
      </div>

      <aside className='assistant-pane'>
        <div className='assistant-title'>AI 助手</div>
        <AiPanel
          selectedPath={selectedPath}
          selectedNode={selectedNode}
          scriptDetail={scriptDetail}
          terminalTranscript={terminalTranscript}
          onAiResult={(result) => {
            setAiReviewContent(result)
            setAiReviewContent(prev => prev) // trigger re-render
          }}
          showToast={showToast}
        />
      </aside>
    </section>
  )
}
