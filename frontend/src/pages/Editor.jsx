import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Loader2, AlertCircle } from "lucide-react"
import HomeSidebar from "../components/layout/HomeSidebar"
import { useAuth } from "../context/AuthContext"
import { useLoading } from "../context/LoadingContext"

const STATIC_EDITOR_ENTRY = "/editor-app/index.html"

const isAbsoluteUrl = (value) => value.startsWith("http://") || value.startsWith("https://")

export default function Editor() {
  const { user, logout } = useAuth()
  const { hideLoading } = useLoading()
  const navigate = useNavigate()
  const [isFrameLoaded, setIsFrameLoaded] = useState(false)
  const [availability, setAvailability] = useState("checking")

  const editorSrc = useMemo(() => {
    const override = import.meta.env.VITE_EDITOR_DEV_URL
    if (override && typeof override === "string" && override.trim().length > 0) {
      return override.trim()
    }
    return STATIC_EDITOR_ENTRY
  }, [])

  // Hide the global loading indicator when editor page mounts
  useEffect(() => {
    hideLoading()
  }, [hideLoading])

  useEffect(() => {
    setIsFrameLoaded(false)

    if (isAbsoluteUrl(editorSrc)) {
      setAvailability("ready")
      return
    }

    let cancelled = false

    fetch(editorSrc, { cache: "no-store" })
      .then((response) => {
        if (!cancelled) {
          setAvailability(response.ok ? "ready" : "error")
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAvailability("error")
        }
      })

    return () => {
      cancelled = true
    }
  }, [editorSrc])

  const handleLogout = async () => {
    await logout()
    navigate("/")
  }

  const shouldShowLoader = availability !== "error" && !isFrameLoaded

  return (
    <div className="h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 overflow-hidden">
      <div className="flex h-full">
        <HomeSidebar active="editor" userEmail={user?.email} onLogout={handleLogout} />
        <main className="flex-1 ml-64 flex flex-col h-full">
          <header className="px-8 pt-8 pb-6 border-b border-purple-100 bg-white/70 backdrop-blur-md flex-shrink-0">
            <h1 className="text-3xl font-bold mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
              Editor
            </h1>
            <p className="text-base text-muted-foreground">
              Launch the Zapcut editor without leaving the dashboard.
            </p>
            {import.meta.env.VITE_EDITOR_DEV_URL ? (
              <p className="mt-2 text-xs text-muted-foreground">
                Using custom editor URL:{" "}
                <span className="font-mono">{import.meta.env.VITE_EDITOR_DEV_URL}</span>
              </p>
            ) : null}
          </header>

          <section className="flex-1 relative bg-gray-950/10 min-h-0">
            {availability === "error" ? (
              <div className="h-full flex flex-col items-center justify-center text-center px-8 py-12">
                <div className="mb-4 rounded-full bg-red-50 p-4 text-red-500">
                  <AlertCircle className="h-8 w-8" />
                </div>
                <h2 className="text-xl font-semibold mb-2">Editor assets not found</h2>
                <p className="text-muted-foreground max-w-xl">
                  Could not locate the built editor at{" "}
                  <code className="font-mono text-sm">/editor-app/index.html</code>. Run{" "}
                  <code className="font-mono text-sm">npm run prepare:editor</code> to build and sync the
                  editor assets from <code className="font-mono text-sm">frontend/app</code>.
                </p>
              </div>
            ) : (
              <>
                {shouldShowLoader ? (
                  <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm">
                    <Loader2 className="h-10 w-10 animate-spin text-purple-500" />
                    <p className="mt-3 text-sm text-muted-foreground">Loading editor…</p>
                  </div>
                ) : null}
                <iframe
                  key={editorSrc}
                  src={editorSrc}
                  title="Zapcut Editor"
                  className="w-full h-full border-0 bg-white"
                  onLoad={() => setIsFrameLoaded(true)}
                  allow="clipboard-read; clipboard-write; accelerometer; autoplay; camera; microphone"
                />
              </>
            )}
          </section>
        </main>
      </div>
    </div>
  )
}

