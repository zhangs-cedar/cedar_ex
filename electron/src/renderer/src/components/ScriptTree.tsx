import { useState } from 'react'
import type { ScriptNode } from '../types/api'

interface Props {
  scripts: ScriptNode[]
  selectedPath: string | null
  searchQuery: string
  onSelect: (node: ScriptNode) => void
}

export function ScriptTree({ scripts, selectedPath, searchQuery, onSelect }: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const toggleExpand = (path: string) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })
  }

  const renderNode = (node: ScriptNode, depth: number): JSX.Element | null => {
    const keyword = searchQuery.toLowerCase()
    const selfMatch = !keyword || node.name.toLowerCase().includes(keyword) || node.path.toLowerCase().includes(keyword)
    const childMatch = node.children?.some(c => {
      const childMatches = (child: ScriptNode): boolean =>
        child.name.toLowerCase().includes(keyword) || child.children?.some(childMatches) || false
      return childMatches(c)
    })
    if (keyword && !selfMatch && !childMatch) return null

    const isExpanded = expanded.has(node.path)
    const hasChildren = node.children && node.children.length > 0
    const isActive = selectedPath === node.path

    return (
      <div key={node.path}>
        <button
          className={`script-item ${node.runnable ? '' : 'disabled'} ${isActive ? 'active' : ''}`}
          style={{ paddingLeft: `${18 + depth * 16}px` }}
          onClick={() => {
            if (node.runnable) onSelect(node)
            if (hasChildren && !node.runnable) toggleExpand(node.path)
          }}
          title={node.path}
        >
          <span className='script-icon'>
            {!node.runnable && hasChildren ? (isExpanded ? '▾' : '▸') : node.runnable ? '▶' : '◇'}
          </span>
          <span className='script-name'>{node.name}</span>
        </button>
        {hasChildren && isExpanded && (
          <div className='script-children' style={{ marginLeft: `${20 + depth * 16}px` }}>
            {node.children!.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <nav className='script-tree'>
      {scripts.length === 0 && <div className='no-result'>暂无脚本</div>}
      {scripts.map(node => renderNode(node, 0))}
    </nav>
  )
}
