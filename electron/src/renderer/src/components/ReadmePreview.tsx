import { useEffect, useRef } from 'react'
import Editor from '@monaco-editor/react'

interface Props {
  doc: string
}

export function ReadmePreview({ doc }: Props) {
  if (!doc) {
    return (
      <div className='empty-state'>
        <div className='empty-icon'>📄</div>
        <h3>README.md 预览</h3>
        <p>当前脚本没有 README.md 说明文档。</p>
        <p style={{ marginTop: 8, fontSize: 12, color: '#888' }}>
          建议在脚本目录下添加 README.md，用于说明用途、参数和示例。
        </p>
      </div>
    )
  }

  // 检测是否包含 mermaid 代码块
  const hasMermaid = /```mermaid/.test(doc)

  return (
    <div className='card' style={{ marginBottom: 0 }}>
      <div className='card-header compact'>
        <h3>README.md 预览</h3>
      </div>
      <div
        className='doc'
        style={{ maxHeight: 'none', minHeight: 400 }}
      >
        <MarkdownRenderer content={doc} />
      </div>
    </div>
  )
}

function MarkdownRenderer({ content }: { content: string }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    const html = renderMarkdown(content)
    ref.current.innerHTML = html

    // 尝试渲染 mermaid
    if (window.mermaid && /```mermaid/.test(content)) {
      try {
        window.mermaid.run({ nodes: ref.current.querySelectorAll('.mermaid') })
      } catch {
        // ignore
      }
    }
  }, [content])

  return <div ref={ref} />
}

function renderMarkdown(md: string): string {
  const lines = md.replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  let inCode = false
  let codeLang = ''
  let codeLines: string[] = []
  let inParagraph = false
  let inList = false
  let listTag = ''

  const flushParagraph = () => {
    if (inParagraph) { html.push('</p>'); inParagraph = false }
  }
  const closeList = () => {
    if (inList) { html.push(`</${listTag}>`); inList = false }
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trimEnd()

    if (trimmed.startsWith('```')) {
      if (inCode) {
        const code = codeLines.join('\n')
        if (codeLang === 'mermaid') {
          html.push(`<div class="mermaid">${escapeHtml(code)}</div>`)
        } else {
          html.push(`<pre><code>${escapeHtml(code)}</code></pre>`)
        }
        inCode = false
        codeLang = ''
        codeLines = []
      } else {
        flushParagraph()
        closeList()
        inCode = true
        codeLang = trimmed.replace(/^```/, '').trim().toLowerCase()
      }
      continue
    }
    if (inCode) { codeLines.push(line); continue }

    if (!trimmed) {
      flushParagraph()
      closeList()
      continue
    }

    // Headings
    const hMatch = trimmed.match(/^(#{1,3})\s+(.+)$/)
    if (hMatch) {
      flushParagraph()
      closeList()
      html.push(`<h${hMatch[1].length}>${hMatch[2]}</h${hMatch[1].length}>`)
      continue
    }

    // Blockquote
    const qMatch = trimmed.match(/^>\s?(.+)$/)
    if (qMatch) {
      flushParagraph()
      closeList()
      html.push(`<blockquote>${inlineMarkdown(qMatch[1])}</blockquote>`)
      continue
    }

    // List items
    const ulMatch = trimmed.match(/^[-*]\s+(.+)$/)
    const olMatch = trimmed.match(/^\d+\.\s+(.+)$/)
    if (ulMatch || olMatch) {
      flushParagraph()
      const tag = ulMatch ? 'ul' : 'ol'
      if (!inList) { html.push(`<${tag}>`); inList = true; listTag = tag }
      if (listTag !== tag) { closeList(); html.push(`<${tag}>`); inList = true; listTag = tag }
      html.push(`<li>${inlineMarkdown((ulMatch || olMatch)![1])}</li>`)
      continue
    }

    // Table
    if (/^\|.+\|$/.test(trimmed)) {
      flushParagraph()
      closeList()
      const cells = trimmed.split('|').slice(1, -1).map(c => `<td>${inlineMarkdown(c.trim())}</td>`).join('')
      html.push(`<table><tr>${cells}</tr></table>`)
      continue
    }

    // Regular paragraph
    if (!inParagraph) { html.push('<p>'); inParagraph = true }
    else html.push(' ')
    html.push(inlineMarkdown(trimmed))
  }

  flushParagraph()
  closeList()
  if (inCode) {
    html.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`)
  }

  return html.join('\n').replace(/<\/table>\n<table>/g, '')
}

function inlineMarkdown(text: string): string {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2">$1</a>')
}

function escapeHtml(s: string): string {
  return String(s).replace(/[&<>"]/g, ch =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch] ?? ch)
  )
}
