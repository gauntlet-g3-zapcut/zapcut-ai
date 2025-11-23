import { useState, useEffect, useRef, SyntheticEvent } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { Button } from "../components/ui/button"
import { GradientButton } from "@/components/ui/gradient-button"
import HomeSidebar from "../components/layout/HomeSidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Plus, Trash2 } from "lucide-react"
import { api } from "../services/api"
import { DEBUG_AUTH } from "../services/supabase"

interface Brand {
  id: string
  title: string
  description: string
  product_image_1_url?: string
  product_image_2_url?: string
  created_at: string
}

// Cache brands using sessionStorage to persist across HMR and component remounts
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes
const BRANDS_CACHE_KEY = 'zapcut_brands_cache'
const BRANDS_CACHE_TIMESTAMP_KEY = 'zapcut_brands_cache_timestamp'

// Helper functions to manage cache in sessionStorage
const getBrandsCache = (): Brand[] | null => {
  try {
    const cached = sessionStorage.getItem(BRANDS_CACHE_KEY)
    return cached ? JSON.parse(cached) : null
  } catch {
    return null
  }
}

const setBrandsCache = (brands: Brand[]): void => {
  try {
    sessionStorage.setItem(BRANDS_CACHE_KEY, JSON.stringify(brands))
    sessionStorage.setItem(BRANDS_CACHE_TIMESTAMP_KEY, Date.now().toString())
  } catch (error) {
    console.warn('[Dashboard] Failed to cache brands:', error)
  }
}

const getCacheTimestamp = (): number | null => {
  try {
    const timestamp = sessionStorage.getItem(BRANDS_CACHE_TIMESTAMP_KEY)
    return timestamp ? parseInt(timestamp, 10) : null
  } catch {
    return null
  }
}

const clearBrandsCache = (): void => {
  try {
    sessionStorage.removeItem(BRANDS_CACHE_KEY)
    sessionStorage.removeItem(BRANDS_CACHE_TIMESTAMP_KEY)
  } catch (error) {
    console.warn('[Dashboard] Failed to clear cache:', error)
  }
}

export default function Dashboard() {
  const { user, logout, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [brands, setBrands] = useState<Brand[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const isFetchingRef = useRef(false)

  useEffect(() => {
    const cachedBrands = getBrandsCache()
    const cachedTimestamp = getCacheTimestamp()

    if (DEBUG_AUTH) {
      console.log('[Dashboard] useEffect triggered with dependencies:', {
        user: !!user,
        authLoading,
        'location.state?.refetch': location.state?.refetch,
        'location.pathname': location.pathname,
        isFetchingRef: isFetchingRef.current,
        hasCache: !!cachedBrands,
        cacheTimestamp: cachedTimestamp,
      })
    }

    // Wait for auth to finish loading and user to be available
    if (authLoading) {
      if (DEBUG_AUTH) console.log('[Dashboard] Auth still loading, waiting...')
      setLoading(true)
      return
    }

    if (!user) {
      if (DEBUG_AUTH) console.log('[Dashboard] No user found, skipping fetch')
      // User not authenticated, redirect will happen via PrivateRoute
      setLoading(false)
      return
    }

    // Prevent concurrent fetches
    if (isFetchingRef.current) {
      if (DEBUG_AUTH) console.log('[Dashboard] Already fetching, skipping...')
      return
    }

    const fetchBrands = async () => {
      if (DEBUG_AUTH) console.log('[Dashboard] Starting fetchBrands function')
      isFetchingRef.current = true

      try {
        // Check if we should force refetch (e.g., after creating a brand)
        const shouldRefetch = location.state?.refetch
        if (DEBUG_AUTH) console.log('[Dashboard] shouldRefetch:', shouldRefetch)

        // Check cache first (unless forced refetch)
        const now = Date.now()
        const cachedBrands = getBrandsCache()
        const cachedTimestamp = getCacheTimestamp()
        const cacheAge = cachedTimestamp ? now - cachedTimestamp : null
        const cacheValid = !shouldRefetch && cachedBrands && cachedTimestamp && cacheAge < CACHE_DURATION

        if (DEBUG_AUTH) {
          console.log('[Dashboard] Cache check:', {
            shouldRefetch,
            hasCache: !!cachedBrands,
            cacheAge: cacheAge ? `${(cacheAge / 1000).toFixed(1)}s` : 'none',
            cacheValid,
            CACHE_DURATION: `${CACHE_DURATION / 1000}s`,
          })
        }

        if (cacheValid) {
          if (DEBUG_AUTH) {
            console.log('[Dashboard] Using cached brands:', {
              count: cachedBrands.length,
              cacheAge: ((now - cachedTimestamp) / 1000).toFixed(1) + 's',
            })
          }
          setBrands(cachedBrands)
          setLoading(false)
          return
        }

        if (shouldRefetch) {
          if (DEBUG_AUTH) console.log('[Dashboard] Force refetching brands (cache invalidated)')
          // Clear the state immediately to prevent re-triggering
          navigate(location.pathname, { replace: true, state: {} })
        }

        if (DEBUG_AUTH) console.log('[Dashboard] Fetching brands from API...')
        setLoading(true)
        setError(null)
        const data = await api.getBrands()

        if (DEBUG_AUTH) {
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
        }

        setBrands(data)
        // Update cache
        setBrandsCache(data)
        if (DEBUG_AUTH) console.log('[Dashboard] Cache updated, timestamp:', getCacheTimestamp())
      } catch (error) {
        console.error("[Dashboard] Failed to fetch brands:", error)
        setError(error.message || "Failed to load brands")
        // Clear cache on error
        clearBrandsCache()
        if (DEBUG_AUTH) console.log('[Dashboard] Cache cleared due to error')
      } finally {
        if (DEBUG_AUTH) console.log('[Dashboard] Fetch complete, resetting isFetchingRef')
        setLoading(false)
        isFetchingRef.current = false
      }
    }

    fetchBrands()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading, location.state?.refetch])

  const handleLogout = async () => {
    // Clear cache on logout
    clearBrandsCache()
    await logout()
    navigate("/")
  }

  const handleDeleteBrand = async (brandId: string, brandTitle: string) => {
    if (!window.confirm(`Are you sure you want to delete "${brandTitle}"? This action cannot be undone.`)) {
      return
    }

    try {
      await api.deleteBrand(brandId)
      // Refresh the brands list and update cache
      const data = await api.getBrands()
      setBrands(data)
      setBrandsCache(data)
    } catch (error) {
      console.error("Failed to delete brand:", error)
      const errorMessage = error instanceof Error ? error.message : "Failed to delete brand"
      alert(errorMessage)
    }
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
                        onLoad={(e: SyntheticEvent<HTMLImageElement>) => {
                          if (DEBUG_AUTH) {
                            console.log('[Dashboard] Brand image loaded successfully:', {
                              brandId: brand.id,
                              brandTitle: brand.title,
                              imageUrl: e.currentTarget.src,
                            })
                          }
                        }}
                        onError={(e: SyntheticEvent<HTMLImageElement>) => {
                          console.error('[Dashboard] Brand image failed to load:', {
                            brandId: brand.id,
                            brandTitle: brand.title,
                            imageUrl: brand.product_image_1_url,
                            fallbackUrl: `https://placehold.co/400x300?text=${encodeURIComponent(brand.title)}`,
                          })
                          // Fallback to placeholder if image fails to load
                          e.currentTarget.src = `https://placehold.co/400x300?text=${encodeURIComponent(brand.title)}`
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

