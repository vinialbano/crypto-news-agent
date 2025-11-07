import { useEffect, useRef, useState, useCallback } from 'react'
import type {
  ChatMessage,
  ConnectionStatus,
  UseWebSocketReturn,
  WebSocketMessage,
} from '@/types/chat'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ask'

export function useWebSocket(): UseWebSocketReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>('disconnected')
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined)
  const currentAssistantMessageRef = useRef<string | null>(null)

  const connect = useCallback(() => {
    if (
      wsRef.current?.readyState === WebSocket.OPEN ||
      wsRef.current?.readyState === WebSocket.CONNECTING
    ) {
      return
    }

    setConnectionStatus('connecting')
    setError(null)

    try {
      const ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        setConnectionStatus('connected')
        setError(null)
      }

      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data)

          switch (data.type) {
            case 'sources':
              // Clear any previous errors on successful response
              setError(null)
              // Store sources for the upcoming assistant message
              if (data.sources) {
                const assistantMessageId = `assistant-${Date.now()}`
                currentAssistantMessageRef.current = assistantMessageId

                setMessages((prev) => [
                  ...prev,
                  {
                    id: assistantMessageId,
                    type: 'assistant',
                    content: '',
                    sources: data.sources,
                    timestamp: new Date(),
                    isStreaming: true,
                  },
                ])
              }
              break

            case 'chunk':
              // Clear errors when first chunk arrives (streaming started successfully)
              setError(null)
              // Append chunk to current assistant message
              if (currentAssistantMessageRef.current && data.content) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === currentAssistantMessageRef.current
                      ? { ...msg, content: msg.content + data.content }
                      : msg,
                  ),
                )
              }
              break

            case 'done':
              // Mark streaming as complete
              if (currentAssistantMessageRef.current) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === currentAssistantMessageRef.current
                      ? { ...msg, isStreaming: false }
                      : msg,
                  ),
                )
                currentAssistantMessageRef.current = null
              }
              break

            case 'error':
              // Add error message to chat inline
              const errorMessage: ChatMessage = {
                id: `error-${Date.now()}`,
                type: 'error',
                content: data.content || 'An error occurred',
                timestamp: new Date(),
              }
              setMessages((prev) => [...prev, errorMessage])
              currentAssistantMessageRef.current = null
              break
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
          setError('Failed to parse server message')
        }
      }

      ws.onerror = () => {
        setConnectionStatus('error')
        setError('WebSocket connection error')
      }

      ws.onclose = () => {
        setConnectionStatus('disconnected')
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, 3000)
      }

      wsRef.current = ws
    } catch (err) {
      setConnectionStatus('error')
      setError('Failed to establish WebSocket connection')
    }
  }, [])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setConnectionStatus('disconnected')
  }, [])

  const sendMessage = useCallback(
    (question: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setError('WebSocket is not connected')
        return
      }

      if (!question.trim()) {
        setError('Question cannot be empty')
        return
      }

      if (question.length > 500) {
        setError('Question is too long (max 500 characters)')
        return
      }

      // Add user message to chat
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        type: 'user',
        content: question,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMessage])

      // Send question to backend
      try {
        wsRef.current.send(JSON.stringify({ question }))
      } catch (err) {
        setError('Failed to send message')
        console.error('Failed to send message:', err)
      }
    },
    [],
  )

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    sendMessage,
    messages,
    connectionStatus,
    error,
  }
}
