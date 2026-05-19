interface Props {
  running: boolean
}

export function StatusBar({ running }: Props) {
  return (
    <footer className='statusbar'>
      <span>
        {running ? '⚡ 脚本运行中...' : 'CedarEx 工作区'}
      </span>
      <span className='right'>
        <span>AI：opencode 就绪</span>
        <span>UTF-8</span>
      </span>
    </footer>
  )
}
