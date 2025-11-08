import { Link } from "@tanstack/react-router"
import { MessageSquare, FileText } from "lucide-react"

function Navbar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 flex h-14 items-center justify-between">
        <Link to="/" className="flex items-center space-x-2">
          <span className="text-xl font-bold font-serif italic">Crypto News Agent</span>
        </Link>

        <div className="flex items-center gap-6">
          <Link
            to="/"
            className="flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary"
            activeProps={{
              className: "text-primary"
            }}
          >
            <MessageSquare className="h-4 w-4" />
            <span>Chat</span>
          </Link>

          <Link
            to="/articles"
            className="flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary"
            activeProps={{
              className: "text-primary"
            }}
          >
            <FileText className="h-4 w-4" />
            <span>Articles</span>
          </Link>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
