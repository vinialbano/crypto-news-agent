import { useEffect, useRef } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useWebSocket } from '@/hooks/useWebSocket'
import { AlertCircle, Wifi, WifiOff } from 'lucide-react'
import { ChatMessage } from './ChatMessage'
import { MessageInput } from './MessageInput'

export function ChatInterface() {
  const { sendMessage, messages, connectionStatus, error } = useWebSocket()
  const viewportRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (viewportRef.current) {
      viewportRef.current.scrollTop = viewportRef.current.scrollHeight
    }
  }, [messages])

  const isConnected = connectionStatus === 'connected'
  const isStreaming = messages.some((msg) => msg.isStreaming)

  const getConnectionBadge = () => {
    switch (connectionStatus) {
      case 'connected':
        return (
          <Badge variant="outline" className="gap-1 text-green-600 border-green-600">
            <Wifi className="w-3 h-3" />
            Connected
          </Badge>
        )
      case 'connecting':
        return (
          <Badge variant="outline" className="gap-1">
            <Wifi className="w-3 h-3 animate-pulse" />
            Connecting...
          </Badge>
        )
      case 'disconnected':
        return (
          <Badge variant="outline" className="gap-1 text-orange-600 border-orange-600">
            <WifiOff className="w-3 h-3" />
            Disconnected
          </Badge>
        )
      case 'error':
        return (
          <Badge variant="destructive" className="gap-1">
            <WifiOff className="w-3 h-3" />
            Error
          </Badge>
        )
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-5xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">Crypto News Chat</h1>
          <p className="text-sm text-muted-foreground">
            Ask questions about cryptocurrency news
          </p>
        </div>
        {getConnectionBadge()}
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Messages Area */}
      <ScrollArea className="flex-1 border rounded-lg mb-4 bg-background">
        <div ref={viewportRef} className="p-4 h-full overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <div className="text-center space-y-2">
                <p className="text-lg font-medium">Welcome to Crypto News Chat!</p>
                <p className="text-sm">
                  Ask any question about cryptocurrency news and get AI-powered
                  answers.
                </p>
              </div>
            </div>
          ) : (
            <div>
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <MessageInput
        onSend={sendMessage}
        disabled={!isConnected || isStreaming}
      />
    </div>
  )
}
