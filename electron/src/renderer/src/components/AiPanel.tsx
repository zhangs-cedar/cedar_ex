import { useState, useCallback } from 'react'
import type { ScriptNode, ScriptDetail, AiAssistPayload, ApiResult } from '../types/api'

interface Props {
  selectedPath: string | null
  selectedNode: ScriptNode | null
  scriptDetail: ScriptDetail | null
  terminalTranscript: string
  onAiResult: (result: string) => void
  showToast: (msg: string) => void
}

type AiAction = 'explain_params' | 'generate_command' | 'diagnose_log' | 'create_template'

const actionLabels: Record<AiAction, string> = {
  explain_params: '解释参数',
  generate_command: '生成命令',
  diagnose_log: '诊断日志',
  create_template: '创建模板',
}

export function AiPanel({ selectedPath, selectedNode, scriptDetail, terminalTranscript, onAiResult, showToast }: Props) {
  const [loading, setLoading] = useState<AiAction | null>(null)

  const doAction = useCallback(async (action: AiAction) => {
    if (!selectedPath || !scriptDetail) {
      showToast('请先选择一个脚本')
      return
    }
    setLoading(action)
    onAiResult('AI 正在处理，请稍候...')

    const payload: AiAssistPayload = {
      action,
      script_path: selectedPath,
      script_name: selectedNode?.name || '',
      fields: scriptDetail.fields,
      config: collectFormValues(),
      doc: scriptDetail.doc,
      terminal_log: terminalTranscript.slice(-16000),
    }

    const res: ApiResult<{ review: string }> = await window.cedar.aiAssist(payload)
    setLoading(null)

    if (res.ok && res.data?.review) {
      onAiResult(res.data.review)
      showToast('AI 处理完成')
    } else {
      onAiResult(`AI 处理失败：${res.error || '未知错误'}`)
      showToast(res.error || 'AI 处理失败')
    }
  }, [selectedPath, selectedNode, scriptDetail, terminalTranscript, onAiResult, showToast])

  const actions: AiAction[] = ['explain_params', 'generate_command', 'diagnose_log', 'create_template']

  return (
    <>
      <div className='card'>
        <h3>快捷动作</h3>
        <div className='quick-actions' style={{ marginTop: 10 }}>
          {actions.map(action => (
            <button
              key={action}
              onClick={() => doAction(action)}
              disabled={loading !== null || !selectedPath}
            >
              {loading === action ? '处理中...' : actionLabels[action]}
            </button>
          ))}
        </div>
      </div>

      {!selectedPath && (
        <div className='card'>
          <h3>上下文</h3>
          <p className='muted' style={{ marginTop: 6 }}>
            脚本说明已移至 README.md 预览。选择脚本后可使用快捷 AI 操作。
          </p>
        </div>
      )}
    </>
  )
}

function collectFormValues(): Record<string, unknown> {
  const values: Record<string, unknown> = {}
  document.querySelectorAll('[data-name]').forEach(el => {
    const name = (el as HTMLElement).dataset.name
    if (!name) return
    const input = el as HTMLInputElement
    const type = (el as HTMLElement).dataset.type
    if (type === 'bool') values[name] = input.checked
    else if (type === 'int') values[name] = input.value === '' ? null : parseInt(input.value, 10)
    else if (type === 'float') values[name] = input.value === '' ? null : Number(input.value)
    else values[name] = input.value
  })
  return values
}
