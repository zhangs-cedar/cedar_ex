interface Props {
  content: string | null
  onClose: () => void
}

export function AiReview({ content, onClose }: Props) {
  if (!content) return null

  return (
    <div className='card ai-review-card' style={{ marginTop: 14 }}>
      <div className='card-header compact'>
        <h3 style={{ color: 'var(--blue)' }}>AI 分析</h3>
        <button className='btn-ghost' onClick={onClose} style={{ padding: '3px 8px', fontSize: 12 }}>
          关闭
        </button>
      </div>
      <div
        className='doc ai-review-content'
        dangerouslySetInnerHTML={{ __html: renderAiMarkdown(content) }}
      />
    </div>
  )
}

function renderAiMarkdown(md: string): string {
  // Simple markdown renderer for AI output
  const lines = md.replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  let inCode = false
  let codeLines: string[] = []

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trimEnd()

    if (trimmed.startsWith('```')) {
      if (inCode) {
        html.push(`<pre><code>${escHtml(codeLines.join('\n'))}</code></pre>`)
        inCode = false
        codeLines = []
      } else {
        inCode = true
      }
      continue
    }
    if (inCode) {
      codeLines.push(line)
      continue
    }

    if (!trimmed) {
      html.push('<br/>')
      continue
    }

    const hMatch = trimmed.match(/^(#{1,3})\s+(.+)$/)
    if (hMatch) {
      html.push(`<h${hMatch[1].length}>${escHtml(hMatch[2])}</h${hMatch[1].length}>`)
      continue
    }

    const liMatch = trimmed.match(/^(\d+\.|[-\*])\s+(.+)$/)
    if (liMatch) {
      html.push(`<li>${escHtml(liMatch[2])}</li>`)
      continue
    }

    html.push(`<p>${inlineMd(escHtml(trimmed))}</p>`)
  }

  if (inCode) {
    html.push(`<pre><code>${escHtml(codeLines.join('\n'))}</code></pre>`)
  }

  return html.join('\n')
}

function inlineMd(s: string): string {
  return s
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
}

function escHtml(s: string): string {
  return String(s).replace(/[&<>]/g, ch =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[ch] ?? ch)
  )
}
