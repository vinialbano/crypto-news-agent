import { createFileRoute, Outlet } from "@tanstack/react-router"

import Navbar from "@/components/Common/Navbar"

export const Route = createFileRoute("/_layout")({
  component: Layout,
})

function Layout() {
  return (
    <div className="flex h-screen flex-col">
      <Navbar />
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 py-6">
          <Outlet />
        </div>
      </div>
    </div>
  )
}

export default Layout
