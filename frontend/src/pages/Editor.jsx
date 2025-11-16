import { useCallback } from "react"
import { useNavigate } from "react-router-dom"

import { EditorFrame } from "../components/EditorFrame"
import { AppSidebar } from "../components/layout/AppSidebar"
import { useAuth } from "../context/AuthContext"
import { PRIMARY_SIDEBAR_LINKS } from "../config/navigation"

export default function Editor() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = useCallback(async () => {
    await logout()
    navigate("/")
  }, [logout, navigate])

  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        <AppSidebar navItems={PRIMARY_SIDEBAR_LINKS} onLogout={handleLogout} userEmail={user?.email} />
        <main className="flex min-h-screen flex-1 flex-col">
          <header className="border-b p-6">
            <h1 className="text-3xl font-bold">Editor</h1>
            <p className="text-muted-foreground">
              Launch the Zapcut desktop editor experience directly inside your workspace.
            </p>
          </header>
          <div className="flex-1">
            <EditorFrame />
          </div>
        </main>
      </div>
    </div>
  )
}

