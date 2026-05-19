import { useRef, useEffect } from 'react'
import Editor, { loader } from '@monaco-editor/react'

interface Props {
  value: string
  language?: string
  onChange?: (value: string) => void
  readOnly?: boolean
  height?: number | string
}

// Configure Monaco theme
loader.init().then(monaco => {
  monaco.editor.defineTheme('cedar-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6A9955' },
      { token: 'keyword', foreground: '569CD6' },
      { token: 'string', foreground: 'CE9178' },
      { token: 'number', foreground: 'B5CEA8' },
    ],
    colors: {
      'editor.background': '#1e1e1e',
      'editor.foreground': '#d4d4d4',
      'editor.lineHighlightBackground': '#2a2d2e',
      'editor.selectionBackground': '#264f78',
      'editorCursor.foreground': '#aeafad',
      'editorLineNumber.foreground': '#858585',
    },
  })
})

export function MonacoEditor({ value, language = 'markdown', onChange, readOnly = true, height = 400 }: Props) {
  return (
    <Editor
      height={height}
      language={language}
      value={value}
      onChange={onChange ? (v) => onChange(v ?? '') : undefined}
      options={{
        readOnly,
        theme: 'cedar-dark',
        fontSize: 13,
        fontFamily: "'SF Mono', Monaco, 'Fira Code', monospace",
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        lineNumbers: 'on',
        renderLineHighlight: 'line',
        automaticLayout: true,
        wordWrap: 'on',
        padding: { top: 8 },
      }}
    />
  )
}
