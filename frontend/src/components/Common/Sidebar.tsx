import { useState } from "react"
import { FaBars } from "react-icons/fa"
import { X } from "lucide-react"

import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerTrigger,
} from "../ui/drawer"
import SidebarItems from "./SidebarItems"
import { Button } from "../ui/button"

const Sidebar = () => {
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* Mobile */}
      <Drawer open={open} onOpenChange={setOpen} direction="left">
        <DrawerTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="absolute z-[100] m-4 md:hidden"
            aria-label="Open Menu"
          >
            <FaBars />
          </Button>
        </DrawerTrigger>
        <DrawerContent className="fixed inset-y-0 left-0 mt-0 h-full w-[320px] rounded-none">
          <div className="relative h-full overflow-y-auto">
            <DrawerClose asChild>
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-4 top-4"
                aria-label="Close Menu"
              >
                <X className="h-4 w-4" />
              </Button>
            </DrawerClose>
            <div className="p-4 pt-12">
              <SidebarItems onClose={() => setOpen(false)} />
            </div>
          </div>
        </DrawerContent>
      </Drawer>

      {/* Desktop */}
      <div className="sticky top-0 hidden h-screen min-w-[320px] bg-gray-50 p-4 dark:bg-gray-900 md:flex">
        <div className="w-full">
          <SidebarItems />
        </div>
      </div>
    </>
  )
}

export default Sidebar
