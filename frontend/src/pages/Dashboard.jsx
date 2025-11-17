import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Plus, Trash2 } from "lucide-react"
import { api } from "../services/api"

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
      try {
        setLoading(true)
        setError(null)
        const data = await api.getBrands()
        setBrands(data)
      } catch (error) {
        console.error("Failed to fetch brands:", error)
        setError(error.message || "Failed to load brands")
      } finally {
        setLoading(false)
      }
    }
    fetchBrands()
  }, [user, authLoading])

  const handleLogout = async () => {
    await logout()
    navigate("/")
  }

  const handleDeleteBrand = async (brandId, brandTitle) => {
    if (!window.confirm(`Are you sure you want to delete "${brandTitle}"? This action cannot be undone.`)) {
      return
    }

    try {
      await api.deleteBrand(brandId)
      // Refresh the brands list
      const data = await api.getBrands()
      setBrands(data)
    } catch (error) {
      console.error("Failed to delete brand:", error)
      const errorMessage = error instanceof Error ? error.message : "Failed to delete brand"
      alert(errorMessage)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-card border-r min-h-screen p-6">
          <div className="mb-8">
            <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              AdCraft AI
            </h2>
          </div>

          <nav className="space-y-2">
            <Button 
              variant="default" 
              className="w-full justify-start"
            >
              Brands
            </Button>
            <Button 
              variant="ghost" 
              className="w-full justify-start"
              onClick={() => navigate("/campaigns")}
            >
              Campaigns
            </Button>
          </nav>

          <div className="mt-auto pt-8">
            <div className="text-sm text-muted-foreground mb-2">
              {user?.email}
            </div>
            <Button variant="outline" size="sm" onClick={handleLogout} className="w-full">
              Logout
            </Button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">Brands</h1>
              <p className="text-muted-foreground">
                See your projects and create new ones under the selected brand.
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
                    <div className="relative">
                      <img
                        src={brand.product_image_1_url}
                        alt={brand.title}
                        className="w-full h-48 object-cover rounded-md mb-4"
                      />
                      <Button
                        variant="destructive"
                        size="sm"
                        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteBrand(brand.id, brand.title)
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
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

