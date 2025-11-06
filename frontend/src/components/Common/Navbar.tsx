import { Link } from "@tanstack/react-router"

function Navbar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <Link to="/" className="flex items-center space-x-2">
          <span className="text-xl font-bold">Crypto News Agent</span>
        </Link>
      </div>
    </nav>
  )
}

export default Navbar
