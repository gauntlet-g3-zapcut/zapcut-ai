import { useNavigate } from "react-router-dom"
import { Button } from "../ui/button"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { id: "brands", label: "Brands", to: "/dashboard" },
  { id: "campaigns", label: "Campaigns", to: "/campaigns" },
  { id: "editor", label: "Editor", to: "/editor" },
]

export default function HomeSidebar({ active, userEmail, onLogout }) {
  const navigate = useNavigate()

  return (
    <aside className="w-64 bg-white/80 backdrop-blur-sm border-r border-purple-100 h-screen p-6 flex flex-col fixed left-0 top-0 overflow-y-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
          AdCut AI
        </h2>
      </div>

      <nav className="space-y-2">
        {NAV_ITEMS.map((item) => (
          <Button
            key={item.id}
            variant="ghost"
            className={cn(
              "w-full justify-start",
              active === item.id ? "font-medium text-purple-900" : "text-foreground"
            )}
            aria-current={active === item.id ? "page" : undefined}
            onClick={() => navigate(item.to)}
          >
            {item.label}
          </Button>
        ))}
      </nav>

      <div className="mt-auto pt-8">
        {userEmail ? (
          <div className="text-sm text-muted-foreground mb-2 break-all">
            {userEmail}
          </div>
        ) : null}
        {onLogout ? (
          <Button
            variant="outline"
            size="sm"
            onClick={onLogout}
            className="w-full bg-transparent hover:bg-red-50 text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
          >
            Logout
          </Button>
        ) : null}
      </div>
    </aside>
  )
}

