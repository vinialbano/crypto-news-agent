export interface MessageSource {
  title: string
  source: string
  url: string
}

export interface ChatMessage {
  id: string
  type: 'user' | 'assistant' | 'error'
  content: string
  sources?: MessageSource[]
  timestamp: Date
  isStreaming?: boolean
}

export type WebSocketMessageType = 'sources' | 'chunk' | 'done' | 'error'

export interface WebSocketMessage {
  type: WebSocketMessageType
  content?: string
  count?: number
  sources?: MessageSource[]
}

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export interface UseWebSocketReturn {
  sendMessage: (question: string) => void
  messages: ChatMessage[]
  connectionStatus: ConnectionStatus
  error: string | null
}
