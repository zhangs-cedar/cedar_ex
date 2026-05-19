interface Props {
  message: string | null
}

export function Toast({ message }: Props) {
  if (!message) return null

  return (
    <div className='toast'>
      {message}
    </div>
  )
}
