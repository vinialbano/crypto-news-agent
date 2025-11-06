import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/")({
  component: HomePage,
})

function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center">
      <h1 className="mb-4 text-4xl font-bold">Crypto News Agent</h1>
      <p className="text-lg text-gray-600 dark:text-gray-400">
        Welcome to your crypto news analysis assistant
      </p>
    </div>
  )
}
