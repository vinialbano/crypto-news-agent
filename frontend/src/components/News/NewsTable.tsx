import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from '@tanstack/react-table'
import { ArrowUpDown, ExternalLink } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { NewsService } from '@/client'
import type { NewsArticlePublic } from '@/client'

const columns: ColumnDef<NewsArticlePublic>[] = [
  {
    accessorKey: 'title',
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        >
          Title
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const article = row.original
      return (
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 hover:underline text-blue-600 dark:text-blue-400"
        >
          <span className="line-clamp-2">{article.title}</span>
          <ExternalLink className="h-3 w-3 flex-shrink-0" />
        </a>
      )
    },
  },
  {
    accessorKey: 'source_name',
    header: 'Source',
    cell: ({ row }) => (
      <Badge variant="outline" className="whitespace-nowrap">
        {row.getValue('source_name')}
      </Badge>
    ),
  },
  {
    accessorKey: 'published_at',
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        >
          Published
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const publishedAt = row.getValue('published_at') as string | null
      const ingestedAt = row.original.ingested_at
      const date = publishedAt || ingestedAt

      if (!date) return <span className="text-gray-400">Unknown</span>

      const formattedDate = new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(new Date(date))

      return (
        <span className="whitespace-nowrap text-sm">
          {formattedDate}
        </span>
      )
    },
    sortingFn: (rowA, rowB) => {
      const dateA = rowA.original.published_at || rowA.original.ingested_at
      const dateB = rowB.original.published_at || rowB.original.ingested_at
      return new Date(dateA).getTime() - new Date(dateB).getTime()
    },
  },
]

export function NewsTable() {
  const [sorting, setSorting] = useState<SortingState>([
    {
      id: 'published_at',
      desc: true, // Most recent first
    },
  ])
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 10,
  })

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['news'],
    queryFn: () => NewsService.getNewsArticles({ limit: 50 }),
  })

  const table = useReactTable({
    data: data?.articles ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    state: {
      sorting,
      pagination,
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading news articles...</p>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-red-500">
          Error loading news: {error instanceof Error ? error.message : 'Unknown error'}
        </p>
      </div>
    )
  }

  if (!data?.articles.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">No news articles found.</p>
      </div>
    )
  }

  return (
    <div className="w-full space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  )
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">
          Showing {pagination.pageIndex * pagination.pageSize + 1} to{' '}
          {Math.min(
            (pagination.pageIndex + 1) * pagination.pageSize,
            data?.count ?? 0
          )}{' '}
          of {data?.count ?? 0} articles
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Previous
          </Button>
          <div className="text-sm text-gray-500">
            Page {pagination.pageIndex + 1} of {table.getPageCount()}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  )
}
