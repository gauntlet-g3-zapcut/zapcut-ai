import { useState, useEffect } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { Button } from "../components/ui/button"
import { GradientButton } from "@/components/ui/gradient-button"
import HomeSidebar from "../components/layout/HomeSidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Plus, Trash2 } from "lucide-react"
import { api } from "../services/api"

// Cache brands in memory to avoid unnecessary API calls
let brandsCache = null
let brandsCacheTimestamp = null
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

export default function Dashboard() {
  const { user, logout, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
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
        // Check if we should force refetch (e.g., after creating a brand)
        const shouldRefetch = location.state?.refetch

        // Check cache first (unless forced refetch)
        const now = Date.now()
        if (!shouldRefetch && brandsCache && brandsCacheTimestamp && (now - brandsCacheTimestamp) < CACHE_DURATION) {
          console.log('[Dashboard] Using cached brands:', {
            count: brandsCache.length,
            cacheAge: ((now - brandsCacheTimestamp) / 1000).toFixed(1) + 's',
          })
          setBrands(brandsCache)
          setLoading(false)
          return
        }

        if (shouldRefetch) {
          console.log('[Dashboard] Force refetching brands (cache invalidated)')
          // Clear the state so we don't refetch on every render
          navigate(location.pathname, { replace: true, state: {} })
        }

        console.log('[Dashboard] Fetching brands from API...')
        setLoading(true)
        setError(null)
        const data = await api.getBrands()

        console.log('[Dashboard] Brands fetched successfully:', {
          count: data.length,
          brands: data.map(b => ({
            id: b.id,
            title: b.title,
            hasImage1: !!b.product_image_1_url,
            hasImage2: !!b.product_image_2_url,
            image1Url: b.product_image_1_url,
            image2Url: b.product_image_2_url,
          })),
        })

        setBrands(data)
        // Update cache
        brandsCache = data
        brandsCacheTimestamp = now
      } catch (error) {
        console.error("[Dashboard] Failed to fetch brands:", error)
        setError(error.message || "Failed to load brands")
        // Clear cache on error
        brandsCache = null
        brandsCacheTimestamp = null
      } finally {
        setLoading(false)
      }
    }
    fetchBrands()
  }, [user, authLoading])

  const handleLogout = async () => {
    // Clear cache on logout
    brandsCache = null
    brandsCacheTimestamp = null
    await logout()
    navigate("/")
  }

  const handleDeleteBrand = async (brandId, brandTitle) => {
    if (!window.confirm(`Are you sure you want to delete "${brandTitle}"? This action cannot be undone.`)) {
      return
    }

    try {
      await api.deleteBrand(brandId)
      // Refresh the brands list and update cache
      const data = await api.getBrands()
      setBrands(data)
      brandsCache = data
      brandsCacheTimestamp = Date.now()
    } catch (error) {
      console.error("Failed to delete brand:", error)
      const errorMessage = error instanceof Error ? error.message : "Failed to delete brand"
      alert(errorMessage)
    }
  }

  // Function to invalidate cache (can be called after creating/updating brands)
  const invalidateBrandsCache = () => {
    brandsCache = null
    brandsCacheTimestamp = null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50">
      <div className="flex">
        <HomeSidebar active="brands" userEmail={user?.email} onLogout={handleLogout} />

        {/* Main Content */}
        <main className="flex-1 p-8 ml-64">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
                Brands
              </h1>
              <p className="text-base text-muted-foreground">
                See your projects and create new ones under the selected brand.
              </p>
            </div>
            <GradientButton onClick={() => navigate("/brands/create")} className="text-sm px-4 py-2">
              <Plus className="mr-2 h-3 w-3" />
              Create Brand
            </GradientButton>
          </div>

          {loading ? (
            <div className="text-center py-12 text-muted-foreground">
              Loading brands...
            </div>
          ) : error ? (
            <Card className="p-12 text-center">
              <CardHeader>
                <CardTitle className="text-2xl mb-2 text-destructive" style={{ fontFamily: "'Playfair Display', serif" }}>
                  Error
                </CardTitle>
                <CardDescription className="text-base">
                  {error}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <GradientButton onClick={() => window.location.reload()}>
                  Retry
                </GradientButton>
              </CardContent>
            </Card>
          ) : brands.length === 0 ? (
            <Card className="p-12 text-center">
              <CardHeader>
                <CardTitle className="text-2xl mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
                  No brands yet
                </CardTitle>
                <CardDescription className="text-base">
                  Create your first brand to start generating video ads
                </CardDescription>
              </CardHeader>
              <CardContent>
                <GradientButton onClick={() => navigate("/brands/create")}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Brand
                </GradientButton>
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
                        src={brand.product_image_1_url || `https://placehold.co/400x300?text=${encodeURIComponent(brand.title)}`}
                        alt={brand.title}
                        className="w-full h-48 object-cover rounded-md mb-4 bg-gray-100"
                        onLoad={(e) => {
                          console.log('[Dashboard] Brand image loaded successfully:', {
                            brandId: brand.id,
                            brandTitle: brand.title,
                            imageUrl: e.target.src,
                          })
                        }}
                        onError={(e) => {
                          console.error('[Dashboard] Brand image failed to load:', {
                            brandId: brand.id,
                            brandTitle: brand.title,
                            imageUrl: brand.product_image_1_url,
                            fallbackUrl: `https://placehold.co/400x300?text=${encodeURIComponent(brand.title)}`,
                          })
                          // Fallback to placeholder if image fails to load
                          e.target.src = `https://placehold.co/400x300?text=${encodeURIComponent(brand.title)}`
                        }}
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-transparent hover:bg-red-50 text-red-600 hover:text-red-700"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteBrand(brand.id, brand.title)
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <CardTitle style={{ fontFamily: "'Playfair Display', serif" }}>
                      {brand.title}
                    </CardTitle>
                    <CardDescription className="text-base line-clamp-1">
                      {brand.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      {brand.campaign_count || 0} campaigns
                    </p>
                    <div className="flex justify-between gap-2">
                      <Button
                        variant="outline"
                        onClick={() => navigate(`/brands/${brand.id}/edit`)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-sm px-4 py-2"
                      >
                        Edit Brand
                      </Button>
                      <GradientButton
                        onClick={() => navigate(`/brands/${brand.id}/chat`)}
                        className="text-sm px-4 py-2"
                      >
                        Create Campaign
                      </GradientButton>
                    </div>
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

