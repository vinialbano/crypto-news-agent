import { createFileRoute } from '@tanstack/react-router'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { NewsTable } from '@/components/News/NewsTable'
import { NewsService } from '@/client'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'

export const Route = createFileRoute('/_layout/articles')({
  component: NewsPage,
})

function NewsPage() {
  const queryClient = useQueryClient()

  const ingestMutation = useMutation({
    mutationFn: (sourceName?: string) =>
      NewsService.triggerManualIngestion({ sourceName }),
    onSuccess: () => {
      // Invalidate and refetch news articles
      queryClient.invalidateQueries({ queryKey: ['news'] })
    },
  })

  const sources = ['DL News', 'The Defiant', 'Cointelegraph']

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3">
        <div>
          <h1 className="text-2xl font-bold font-serif italic">Recent Articles</h1>
          <p className="text-sm text-muted-foreground">
            Latest cryptocurrency news from trusted sources
          </p>
        </div>
        <div className="flex gap-2">
          {sources.map((source) => (
            <Button
              key={source}
              variant="outline"
              size="sm"
              onClick={() => ingestMutation.mutate(source)}
              disabled={ingestMutation.isPending}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${ingestMutation.isPending && ingestMutation.variables === source ? 'animate-spin' : ''}`} />
              Ingest {source}
            </Button>
          ))}
        </div>
      </div>
      <NewsTable />
    </div>
  )
}
