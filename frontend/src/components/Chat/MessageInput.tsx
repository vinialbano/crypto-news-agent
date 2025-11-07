import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send } from 'lucide-react'

interface MessageInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [input, setInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim() || disabled) {
      return
    }

    onSend(input.trim())
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about cryptocurrency news..."
        disabled={disabled}
        maxLength={500}
        className="flex-1"
        autoComplete="off"
      />
      <Button
        type="submit"
        disabled={disabled || !input.trim()}
        size="icon"
        className="flex-shrink-0"
      >
        <Send className="w-4 h-4" />
      </Button>
    </form>
  )
}
