import { useLocation, useNavigate } from "react-router-dom"

import { Button } from "../ui/button"
import { cn } from "../../lib/utils"

const DEFAULT_NAV_ITEMS = []

export function AppSidebar({
  brandName = "AdCraft AI",
  navItems = DEFAULT_NAV_ITEMS,
  onLogout,
  userEmail,
}) {
  const location = useLocation()
  const navigate = useNavigate()

  const handleSelect = (item) => {
    if (item.disabled) {
      return
    }

    if (typeof item.onSelect === "function") {
      item.onSelect({ navigate, location })
      return
    }

    if (item.path) {
      if (item.search) {
        navigate({ pathname: item.path, search: item.search })
      } else {
        navigate(item.path)
      }
    }
  }

  return (
    <aside className="w-64 bg-card border-r min-h-screen p-6 flex flex-col">
      <div className="mb-8">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
          {brandName}
        </h2>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => {
          const isActive = item.isActive ? item.isActive(location) : item.path === location.pathname

          return (
            <Button
              key={item.key}
              variant={isActive ? "secondary" : "ghost"}
              className={cn("w-full justify-start", item.disabled && "cursor-not-allowed opacity-60")}
              onClick={() => handleSelect(item)}
              disabled={item.disabled}
            >
              {item.label}
            </Button>
          )
        })}
      </nav>

      {onLogout ? (
        <div className="mt-auto pt-8">
          {userEmail ? <div className="text-sm text-muted-foreground mb-2">{userEmail}</div> : null}
          <Button variant="outline" size="sm" onClick={onLogout} className="w-full">
            Logout
          </Button>
        </div>
      ) : null}
    </aside>
  )
}

