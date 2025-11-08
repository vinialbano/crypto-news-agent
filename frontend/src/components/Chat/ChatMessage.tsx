import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Card, CardContent } from '@/components/ui/card'
import type { ChatMessage as ChatMessageType } from '@/types/chat'
import { AlertCircle, Bot, User } from 'lucide-react'

interface ChatMessageProps {
  message: ChatMessageType
}

export function ChatMessage({ message }: ChatMessageProps) {
  // Handle error messages differently
  if (message.type === 'error') {
    return (
      <div className="flex justify-center mb-4">
        <Card className="bg-destructive/10 border-destructive/50 max-w-[80%]">
          <CardContent className="p-3 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-destructive">{message.content}</p>
              <span className="text-xs text-destructive/70 mt-1 block">
                {message.timestamp.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const isUser = message.type === 'user'

  return (
    <div
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-4`}
    >
      <Avatar className="w-8 h-8 flex-shrink-0">
        <AvatarFallback className={isUser ? 'bg-blue-500' : 'bg-purple-500'}>
          {isUser ? (
            <User className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-white" />
          )}
        </AvatarFallback>
      </Avatar>

      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[80%]`}>
        <Card
          className={`${isUser ? 'bg-blue-500 text-white' : 'bg-muted'} border-none shadow-sm`}
        >
          <CardContent className="p-3">
            {message.sources && message.sources.length > 0 && (
              <div className="mb-3 pb-3 border-b border-border/50">
                <p className="text-xs font-medium mb-2 opacity-75">
                  Sources ({message.sources.length}):
                </p>
                <ul className="text-xs space-y-1">
                  {message.sources.map((source, idx) => (
                    <li key={idx}>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:underline opacity-90 hover:opacity-100 text-blue-600 hover:text-blue-800"
                      >
                        {source.title} - {source.source}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-sm whitespace-pre-wrap break-words">
              {message.content || (message.isStreaming && (
                <span className="italic opacity-70 animate-pulse">Thinking...</span>
              ))}
              {message.isStreaming && message.content && (
                <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
              )}
            </p>
          </CardContent>
        </Card>
        <span className="text-xs text-muted-foreground mt-1 px-1">
          {message.timestamp.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
    </div>
  )
}


