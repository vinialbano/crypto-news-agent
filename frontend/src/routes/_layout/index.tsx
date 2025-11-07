import { createFileRoute } from "@tanstack/react-router"
import { ChatInterface } from "@/components/Chat/ChatInterface"

export const Route = createFileRoute("/_layout/")({
  component: HomePage,
})

function HomePage() {
  return <ChatInterface />
}
