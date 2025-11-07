import { createFileRoute } from '@tanstack/react-router'
import { NewsTable } from '@/components/News/NewsTable'

export const Route = createFileRoute('/_layout/articles')({
  component: NewsPage,
})

function NewsPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold font-serif italic">Recent Articles</h1>
        <p className="text-sm text-muted-foreground">
          Latest cryptocurrency news from trusted sources
        </p>
      </div>
      <NewsTable />
    </div>
  )
}
