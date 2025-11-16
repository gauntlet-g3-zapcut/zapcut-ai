import { useState, useEffect, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Plus } from "lucide-react"
import { api } from "../services/api"
import { AppSidebar } from "../components/layout/AppSidebar"
import { PRIMARY_SIDEBAR_LINKS } from "../config/navigation"

export default function Dashboard() {
  const { user, logout, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [brands, setBrands] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Wait for auth to finish loading and user to be available
    if (authLoading) {
      setLoading(true)
      return
    }

    if (!user) {
      // User not authenticated, redirect will happen via PrivateRoute
      setLoading(false)
      return
    }

    const fetchBrands = async () => {
      // Only fetch if user is authenticated
      if (!user) {
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError(null)
        const data = await api.getBrands()
        setBrands(data)
      } catch (error) {
        console.error("Failed to fetch brands:", error)
        // Silently handle authentication errors
        if (error.message && error.message.includes("token")) {
          console.log("User not authenticated, skipping brands fetch")
        } else {
          setError(error.message || "Failed to load brands")
        }
      } finally {
        setLoading(false)
      }
    }
    fetchBrands()
  }, [user, authLoading])

  const handleLogout = useCallback(async () => {
    await logout()
    navigate("/")
  }, [logout, navigate])

  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        <AppSidebar navItems={PRIMARY_SIDEBAR_LINKS} onLogout={handleLogout} userEmail={user?.email} />

        {/* Main Content */}
        <main className="flex-1 p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">Brands</h1>
              <p className="text-muted-foreground">
                See your projects and create new ones under the selected brand!
              </p>
            </div>
            <Button onClick={() => navigate("/brands/create")}>
              <Plus className="mr-2 h-4 w-4" />
              Create Brand
            </Button>
          </div>

          {loading ? (
            <div className="text-center py-12 text-muted-foreground">
              Loading brands...
            </div>
          ) : error ? (
            <Card className="p-12 text-center">
              <CardHeader>
                <CardTitle className="text-2xl mb-2 text-destructive">Error</CardTitle>
                <CardDescription>
                  {error}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button onClick={() => window.location.reload()}>
                  Retry
                </Button>
              </CardContent>
            </Card>
          ) : brands.length === 0 ? (
            <Card className="p-12 text-center">
              <CardHeader>
                <CardTitle className="text-2xl mb-2">No brands yet</CardTitle>
                <CardDescription>
                  Create your first brand to start generating video ads
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button onClick={() => navigate("/brands/create")}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Brand
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {brands.map((brand) => (
                <Card
                  key={brand.id}
                  className="group relative hover:shadow-lg transition-all"
                >
                  <CardHeader>
                    <img
                      src={brand.product_image_1_url}
                      alt={brand.title}
                      className="w-full h-48 object-cover rounded-md mb-4"
                    />
                    <CardTitle>{brand.title}</CardTitle>
                    <CardDescription>{brand.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      {brand.campaign_count || 0} campaigns
                    </p>
                    <Button
                      onClick={() => navigate(`/brands/${brand.id}/chat`)}
                      className="w-full opacity-0 group-hover:opacity-100 transition-opacity"
                      size="sm"
                    >
                      Create Campaign
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

