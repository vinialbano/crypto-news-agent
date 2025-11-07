import { createFileRoute } from '@tanstack/react-router'
import { NewsTable } from '@/components/News/NewsTable'

export const Route = createFileRoute('/_layout/news')({
  component: NewsPage,
})

function NewsPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-3xl font-bold">Crypto News</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Latest cryptocurrency news from trusted sources
        </p>
      </div>
      <NewsTable />
    </div>
  )
}
