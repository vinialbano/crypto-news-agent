import { Link as RouterLink } from "@tanstack/react-router"
import { FiHome, FiFileText } from "react-icons/fi"

const items = [
  { icon: FiHome, title: "Home", path: "/" },
  { icon: FiFileText, title: "News", path: "/news" },
]

interface SidebarItemsProps {
  onClose?: () => void
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const listItems = items.map(({ icon: Icon, title, path }) => (
    <RouterLink key={title} to={path} onClick={onClose}>
      <div className="flex items-center gap-4 px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-800">
        <Icon className="h-4 w-4" />
        <span>{title}</span>
      </div>
    </RouterLink>
  ))

  return (
    <>
      <div className="px-4 py-2 text-xs font-bold">Menu</div>
      <div>{listItems}</div>
    </>
  )
}

export default SidebarItems
