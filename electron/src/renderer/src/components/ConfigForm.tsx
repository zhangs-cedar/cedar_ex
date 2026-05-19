import { useCallback, useRef, useEffect, useState } from 'react'
import type { ScriptField } from '../types/api'

interface Props {
  fields: ScriptField[]
  onRun: (config: Record<string, unknown>) => void
  onStop: () => void
  onReset: () => void
  running: boolean
  selectedPath: string
}

export function ConfigForm({ fields, onRun, onStop, onReset, running, selectedPath }: Props) {
  const formRef = useRef<HTMLFormElement>(null)
  const [config, setConfig] = useState<Record<string, unknown>>({})

  useEffect(() => {
    // 初始化表单默认值
    const defaults: Record<string, unknown> = {}
    fields.forEach(f => {
      defaults[f.name] = f.default ?? (f.type === 'bool' ? false : '')
    })
    setConfig(defaults)
  }, [fields])

  const updateField = useCallback((name: string, value: unknown) => {
    setConfig(prev => ({ ...prev, [name]: value }))
  }, [])

  const handleRun = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    onRun(config)
  }, [config, onRun])

  const handleReset = useCallback(() => {
    const defaults: Record<string, unknown> = {}
    fields.forEach(f => {
      defaults[f.name] = f.default ?? (f.type === 'bool' ? false : '')
    })
    setConfig(defaults)
    onReset()
  }, [fields, onReset])

  if (!fields || fields.length === 0) {
    return (
      <div className='card'>
        <div className='card-header'>
          <div>
            <h3>参数配置</h3>
            <p className='muted'>该脚本没有参数配置，点击「运行脚本」即可执行。</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type='button' className='btn-primary' onClick={() => onRun(config)} disabled={running}>
              ▶ 运行脚本
            </button>
            <button type='button' className='btn-danger' onClick={onStop}>停止 / Ctrl+C</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className='card'>
      <div className='card-header'>
        <div>
          <h3>参数配置</h3>
          <p className='muted'>由 form.yaml 生成，可保存为运行预设。</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type='button' className='btn-ghost' onClick={handleReset}>重置</button>
          <button type='button' className='btn-primary' onClick={handleRun} disabled={running}>
            ▶ 运行脚本
          </button>
          <button type='button' className='btn-danger' onClick={onStop}>停止 / Ctrl+C</button>
        </div>
      </div>
      <form ref={formRef} className='form-grid' onSubmit={handleRun}>
        {fields.map(field => (
          <FormField
            key={field.name}
            field={field}
            value={config[field.name]}
            onChange={(v) => updateField(field.name, v)}
          />
        ))}
      </form>
    </div>
  )
}

function FormField({ field, value, onChange }: { field: ScriptField; value: unknown; onChange: (v: unknown) => void }) {
  const type = normalizeType(field.type)

  if (type === 'doc') return null

  if (type === 'bool') {
    return (
      <div className='field'>
        <label>
          <input
            type='checkbox'
            checked={Boolean(value)}
            onChange={e => onChange(e.target.checked)}
          />
          <span>{field.label || field.name}</span>
          {field.required && <span style={{ color: 'var(--danger)' }}>*</span>}
        </label>
        {field.description && <small>{field.description}</small>}
      </div>
    )
  }

  if (type === 'file' || type === 'dir') {
    return (
      <div className='field full'>
        <label>
          {field.label || field.name}
          {field.required && <span style={{ color: 'var(--danger)' }}>*</span>}
          <span style={{ color: '#858585', fontSize: 11, marginLeft: 'auto' }}>{type}</span>
        </label>
        <div className='field-row'>
          <input
            type='text'
            value={String(value ?? '')}
            onChange={e => onChange(e.target.value)}
            placeholder={type === 'dir' ? '选择或输入目录路径' : '选择或输入文件路径'}
            data-name={field.name}
            data-type={type}
          />
          <button type='button' onClick={async () => {
            const res = type === 'dir' ? await window.cedar.chooseDirectory() : await window.cedar.chooseFile()
            if (res.ok && res.data) onChange(res.data)
          }}>
            {type === 'dir' ? '选择目录' : '选择文件'}
          </button>
        </div>
        {field.description && <small>{field.description}</small>}
      </div>
    )
  }

  if (type === 'multiline') {
    return (
      <div className='field full'>
        <label>
          {field.label || field.name}
          {field.required && <span style={{ color: 'var(--danger)' }}>*</span>}
        </label>
        <textarea
          value={String(value ?? '')}
          onChange={e => onChange(e.target.value)}
          data-name={field.name}
          data-type={type}
        />
        {field.description && <small>{field.description}</small>}
      </div>
    )
  }

  if (type === 'select') {
    return (
      <div className='field'>
        <label>
          {field.label || field.name}
          {field.required && <span style={{ color: 'var(--danger)' }}>*</span>}
        </label>
        <select
          value={String(value ?? '')}
          onChange={e => onChange(e.target.value)}
          data-name={field.name}
          data-type={type}
        >
          {(field.options || []).map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        {field.description && <small>{field.description}</small>}
      </div>
    )
  }

  return (
    <div className='field'>
      <label>
        {field.label || field.name}
        {field.required && <span style={{ color: 'var(--danger)' }}>*</span>}
      </label>
      <input
        type={type === 'int' || type === 'float' ? 'number' : type === 'date' ? 'date' : 'text'}
        value={String(value ?? '')}
        onChange={e => onChange(type === 'int' ? (e.target.value === '' ? null : parseInt(e.target.value, 10)) : type === 'float' ? (e.target.value === '' ? null : Number(e.target.value)) : e.target.value)}
        min={field.min}
        max={field.max}
        step={type === 'float' ? 'any' : undefined}
        data-name={field.name}
        data-type={type}
      />
      {field.description && <small>{field.description}</small>}
    </div>
  )
}

function normalizeType(t: string): string {
  if (t === 'string') return 'text'
  return t || 'text'
}
