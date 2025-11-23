import { useState, useEffect, useRef, SyntheticEvent } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { useLoading } from "../context/LoadingContext"
import { Button } from "../components/ui/button"
import { GradientButton } from "@/components/ui/gradient-button"
import HomeSidebar from "../components/layout/HomeSidebar"
import { Card, CardContent } from "../components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu"
import { Plus, Trash2, ChevronDown, ChevronRight, Play, Clock, CheckCircle2, XCircle, Loader2, FileEdit, MoreVertical } from "lucide-react"
import { api } from "../services/api"
import { DEBUG_AUTH } from "../services/supabase"
import { prepareEditorProject } from "../lib/editor-bridge"

interface Campaign {
  id: string
  brand_id: string
  brand_title: string
  status: string
  final_video_url?: string
  created_at: string
  video_urls_count: number
}

interface Brand {
  id: string
  title: string
  description: string
  product_image_1_url?: string
  product_image_2_url?: string
  created_at: string
  campaign_count?: number
  campaigns?: Campaign[]
}

// Cache brands using sessionStorage to persist across HMR and component remounts
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes
const BRANDS_CACHE_KEY = 'zapcut_brands_campaigns_cache'
const BRANDS_CACHE_TIMESTAMP_KEY = 'zapcut_brands_campaigns_cache_timestamp'

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
    console.warn('[BrandsCampaignsList] Failed to cache brands:', error)
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
    console.warn('[BrandsCampaignsList] Failed to clear cache:', error)
  }
}

export default function BrandsCampaignsList() {
  const { user, logout, loading: authLoading } = useAuth()
  const { showLoading, hideLoading } = useLoading()
  const navigate = useNavigate()
  const location = useLocation()
  const [brands, setBrands] = useState<Brand[]>([])
  const [expandedBrands, setExpandedBrands] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [addingToEditor, setAddingToEditor] = useState<string | null>(null)
  const isFetchingRef = useRef(false)

  useEffect(() => {
    const cachedBrands = getBrandsCache()
    const cachedTimestamp = getCacheTimestamp()

    if (DEBUG_AUTH) {
      console.log('[BrandsCampaignsList] useEffect triggered with dependencies:', {
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
      if (DEBUG_AUTH) console.log('[BrandsCampaignsList] Auth still loading, waiting...')
      setLoading(true)
      return
    }

    if (!user) {
      if (DEBUG_AUTH) console.log('[BrandsCampaignsList] No user found, skipping fetch')
      setLoading(false)
      return
    }

    // Prevent concurrent fetches
    if (isFetchingRef.current) {
      if (DEBUG_AUTH) console.log('[BrandsCampaignsList] Already fetching, skipping...')
      return
    }

    const fetchBrandsAndCampaigns = async () => {
      if (DEBUG_AUTH) console.log('[BrandsCampaignsList] Starting fetch function')
      isFetchingRef.current = true

      try {
        // Check if we should force refetch
        const shouldRefetch = location.state?.refetch
        if (DEBUG_AUTH) console.log('[BrandsCampaignsList] shouldRefetch:', shouldRefetch)

        // Check cache first (unless forced refetch)
        const now = Date.now()
        const cachedBrands = getBrandsCache()
        const cachedTimestamp = getCacheTimestamp()
        const cacheAge = cachedTimestamp ? now - cachedTimestamp : null
        const cacheValid = !shouldRefetch && cachedBrands && cachedTimestamp && cacheAge < CACHE_DURATION

        if (DEBUG_AUTH) {
          console.log('[BrandsCampaignsList] Cache check:', {
            shouldRefetch,
            hasCache: !!cachedBrands,
            cacheAge: cacheAge ? `${(cacheAge / 1000).toFixed(1)}s` : 'none',
            cacheValid,
            CACHE_DURATION: `${CACHE_DURATION / 1000}s`,
          })
        }

        if (cacheValid) {
          if (DEBUG_AUTH) {
            console.log('[BrandsCampaignsList] Using cached brands:', {
              count: cachedBrands.length,
              cacheAge: ((now - cachedTimestamp) / 1000).toFixed(1) + 's',
            })
          }
          setBrands(cachedBrands)
          setLoading(false)
          return
        }

        if (shouldRefetch) {
          if (DEBUG_AUTH) console.log('[BrandsCampaignsList] Force refetching brands (cache invalidated)')
          navigate(location.pathname, { replace: true, state: {} })
        }

        if (DEBUG_AUTH) console.log('[BrandsCampaignsList] Fetching brands and campaigns from API...')
        setLoading(true)
        setError(null)

        // Fetch brands and campaigns
        const [brandsData, campaignsData] = await Promise.all([
          api.getBrands<Brand[]>(),
          api.getAllCampaigns<Campaign[]>()
        ])

        // Group campaigns by brand_id
        const campaignsByBrand = campaignsData.reduce((acc, campaign) => {
          if (!acc[campaign.brand_id]) {
            acc[campaign.brand_id] = []
          }
          acc[campaign.brand_id].push(campaign)
          return acc
        }, {} as Record<string, Campaign[]>)

        // Combine brands with their campaigns
        const brandsWithCampaigns = brandsData.map(brand => ({
          ...brand,
          campaigns: campaignsByBrand[brand.id] || []
        }))

        if (DEBUG_AUTH) {
          console.log('[BrandsCampaignsList] Data fetched successfully:', {
            brandsCount: brandsWithCampaigns.length,
            totalCampaigns: campaignsData.length,
          })
        }

        setBrands(brandsWithCampaigns)
        // Update cache
        setBrandsCache(brandsWithCampaigns)
        if (DEBUG_AUTH) console.log('[BrandsCampaignsList] Cache updated, timestamp:', getCacheTimestamp())
      } catch (error) {
        console.error("[BrandsCampaignsList] Failed to fetch data:", error)
        setError((error as Error).message || "Failed to load data")
        clearBrandsCache()
        if (DEBUG_AUTH) console.log('[BrandsCampaignsList] Cache cleared due to error')
      } finally {
        if (DEBUG_AUTH) console.log('[BrandsCampaignsList] Fetch complete, resetting isFetchingRef')
        setLoading(false)
        isFetchingRef.current = false
      }
    }

    fetchBrandsAndCampaigns()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading, location.state?.refetch])

  const handleLogout = async () => {
    clearBrandsCache()
    await logout()
    navigate("/")
  }

  const toggleBrand = (brandId: string) => {
    setExpandedBrands(prev => {
      const newSet = new Set(prev)
      if (newSet.has(brandId)) {
        newSet.delete(brandId)
      } else {
        newSet.add(brandId)
      }
      return newSet
    })
  }

  const handleDeleteBrand = async (brandId: string, brandTitle: string) => {
    if (!window.confirm(`Are you sure you want to delete "${brandTitle}"? This action cannot be undone.`)) {
      return
    }

    try {
      await api.deleteBrand(brandId)
      // Refresh the brands list and update cache
      const [brandsData, campaignsData] = await Promise.all([
        api.getBrands<Brand[]>(),
        api.getAllCampaigns<Campaign[]>()
      ])

      const campaignsByBrand = campaignsData.reduce((acc, campaign) => {
        if (!acc[campaign.brand_id]) {
          acc[campaign.brand_id] = []
        }
        acc[campaign.brand_id].push(campaign)
        return acc
      }, {} as Record<string, Campaign[]>)

      const brandsWithCampaigns = brandsData.map(brand => ({
        ...brand,
        campaigns: campaignsByBrand[brand.id] || []
      }))

      setBrands(brandsWithCampaigns)
      setBrandsCache(brandsWithCampaigns)
    } catch (error) {
      console.error("Failed to delete brand:", error)
      const errorMessage = error instanceof Error ? error.message : "Failed to delete brand"
      alert(errorMessage)
    }
  }

  const handleDeleteCampaign = async (campaignId: string, e: React.MouseEvent) => {
    e.stopPropagation()

    if (!confirm("Are you sure you want to delete this campaign? This action cannot be undone.")) {
      return
    }

    setDeleting(campaignId)
    try {
      await api.deleteCampaign(campaignId)
      // Refresh the list
      const [brandsData, campaignsData] = await Promise.all([
        api.getBrands<Brand[]>(),
        api.getAllCampaigns<Campaign[]>()
      ])

      const campaignsByBrand = campaignsData.reduce((acc, campaign) => {
        if (!acc[campaign.brand_id]) {
          acc[campaign.brand_id] = []
        }
        acc[campaign.brand_id].push(campaign)
        return acc
      }, {} as Record<string, Campaign[]>)

      const brandsWithCampaigns = brandsData.map(brand => ({
        ...brand,
        campaigns: campaignsByBrand[brand.id] || []
      }))

      setBrands(brandsWithCampaigns)
      setBrandsCache(brandsWithCampaigns)
    } catch (error) {
      console.error("Failed to delete campaign:", error)
      alert("Failed to delete campaign. Please try again.")
    } finally {
      setDeleting(null)
    }
  }

  const handleAddAllVideosToEditor = async (brand: Brand, e: React.MouseEvent) => {
    e.stopPropagation()

    const campaigns = brand.campaigns || []

    // Show global loading indicator
    showLoading("Loading videos into editor...")
    setAddingToEditor(brand.id)

    try {
      // Gather all completed videos from all campaigns
      const allVideos: Array<{ url: string; name: string; order: number; campaignId: string; sceneNumber?: number }> = []

      for (const campaign of campaigns) {
        if (campaign.status === "completed") {
          try {
            // Fetch campaign status to get the scenes with video URLs
            const campaignStatus: any = await api.getCampaignStatus(campaign.id)
            const scenes = campaignStatus?.progress?.scenes || []

            scenes.forEach((scene: any, index: number) => {
              if (scene.status === "completed" && scene.video_url) {
                allVideos.push({
                  url: scene.video_url,
                  name: scene.title?.trim() || `${brand.title} - Scene ${scene.scene_number ?? index + 1}`,
                  order: allVideos.length + 1,
                  campaignId: campaign.id,
                  sceneNumber: scene.scene_number
                })
              }
            })
          } catch (error) {
            console.error(`Failed to fetch campaign ${campaign.id}:`, error)
          }
        }
      }

      if (allVideos.length === 0) {
        hideLoading()
        alert("No completed videos found for this brand.")
        return
      }

      await prepareEditorProject({
        projectName: `${brand.title} - All Videos`,
        videos: allVideos.map((video, index) => ({
          url: video.url,
          name: video.name,
          order: index + 1,
          sceneNumber: video.sceneNumber
        }))
      })

      navigate("/editor")
    } catch (error) {
      console.error("Failed to add videos to editor:", error)
      hideLoading()
      alert("Failed to add videos to editor. Please try again.")
    } finally {
      setAddingToEditor(null)
      // Note: We don't hide loading here because navigation will unmount this component
      // The loading indicator will be hidden when the editor page mounts
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />
      case "processing":
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      case "draft":
        return <FileEdit className="h-4 w-4 text-purple-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "completed":
        return "Completed"
      case "failed":
        return "Failed"
      case "processing":
        return "Generating"
      case "pending":
        return "Pending"
      case "draft":
        return "Draft - Review Storyline"
      default:
        return status
    }
  }

  const handleCampaignClick = (campaign: Campaign) => {
    if (campaign.status === "draft") {
      navigate(`/campaigns/${campaign.id}/storyline`)
    } else if (campaign.status === "completed" && campaign.final_video_url) {
      navigate(`/campaigns/${campaign.id}/video`)
    } else if (campaign.status === "processing" || campaign.status === "pending") {
      navigate(`/campaigns/${campaign.id}/progress`)
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
                Brands & Campaigns
              </h1>
              <p className="text-base text-muted-foreground">
                Manage your brands and view all generated campaigns
              </p>
            </div>
            <GradientButton onClick={() => navigate("/brands/create")} className="text-sm px-4 py-2">
              <Plus className="mr-2 h-3 w-3" />
              Create Brand
            </GradientButton>
          </div>

          {loading ? (
            <div className="text-center py-12 text-muted-foreground">
              Loading...
            </div>
          ) : error ? (
            <Card className="p-12 text-center">
              <CardContent>
                <h2 className="text-2xl mb-2 text-destructive" style={{ fontFamily: "'Playfair Display', serif" }}>
                  Error
                </h2>
                <p className="text-base text-muted-foreground mb-4">
                  {error}
                </p>
                <GradientButton onClick={() => window.location.reload()}>
                  Retry
                </GradientButton>
              </CardContent>
            </Card>
          ) : brands.length === 0 ? (
            <Card className="p-12 text-center">
              <CardContent>
                <h2 className="text-2xl mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
                  No brands yet
                </h2>
                <p className="text-base text-muted-foreground mb-4">
                  Create your first brand to start generating video ads
                </p>
                <GradientButton onClick={() => navigate("/brands/create")}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Brand
                </GradientButton>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {brands.map((brand) => {
                const isExpanded = expandedBrands.has(brand.id)
                const campaigns = brand.campaigns || []

                return (
                  <Card key={brand.id} className="overflow-hidden">
                    {/* Brand Header - Clickable to expand/collapse */}
                    <div
                      className="flex items-center gap-4 p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                      onClick={() => toggleBrand(brand.id)}
                    >
                      {/* Expand/Collapse Icon */}
                      <div className="flex-shrink-0">
                        {isExpanded ? (
                          <ChevronDown className="h-5 w-5 text-gray-500" />
                        ) : (
                          <ChevronRight className="h-5 w-5 text-gray-500" />
                        )}
                      </div>

                      {/* Brand Image */}
                      <div className="flex-shrink-0">
                        <img
                          src={brand.product_image_1_url || `https://placehold.co/80x80?text=${encodeURIComponent(brand.title)}`}
                          alt={brand.title}
                          className="w-20 h-20 object-cover rounded-md bg-gray-100"
                          onLoad={(e: SyntheticEvent<HTMLImageElement>) => {
                            if (DEBUG_AUTH) {
                              console.log('[BrandsCampaignsList] Brand image loaded:', brand.title)
                            }
                          }}
                          onError={(e: SyntheticEvent<HTMLImageElement>) => {
                            console.error('[BrandsCampaignsList] Brand image failed to load:', brand.title)
                            e.currentTarget.src = `https://placehold.co/80x80?text=${encodeURIComponent(brand.title)}`
                          }}
                        />
                      </div>

                      {/* Brand Info */}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl font-bold mb-1" style={{ fontFamily: "'Playfair Display', serif" }}>
                          {brand.title}
                        </h3>
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          {brand.description}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {campaigns.length} campaign{campaigns.length !== 1 ? 's' : ''}
                        </p>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <GradientButton
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/brands/${brand.id}/chat`)
                          }}
                          className="text-sm px-4 py-2"
                        >
                          <Plus className="mr-2 h-3 w-3" />
                          New Campaign
                        </GradientButton>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => e.stopPropagation()}
                              className="h-8 w-8 p-0"
                            >
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation()
                                navigate(`/brands/${brand.id}/edit`)
                              }}
                            >
                              <FileEdit className="mr-2 h-4 w-4" />
                              Edit Brand
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => handleAddAllVideosToEditor(brand, e)}
                              disabled={addingToEditor === brand.id}
                            >
                              {addingToEditor === brand.id ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              ) : (
                                <Play className="mr-2 h-4 w-4" />
                              )}
                              Add All Videos to Editor
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDeleteBrand(brand.id, brand.title)
                              }}
                              className="text-red-600 focus:text-red-600 focus:bg-red-50"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete Brand
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>

                    {/* Campaigns List - Shown when expanded */}
                    {isExpanded && campaigns.length > 0 && (
                      <div className="border-t border-gray-100 bg-gray-50/50">
                        <div className="p-4 pl-24 space-y-3">
                          {campaigns.map((campaign) => (
                            <div
                              key={campaign.id}
                              className="flex items-center gap-4 p-3 bg-white rounded-lg hover:shadow-md transition-shadow cursor-pointer border border-gray-100"
                              onClick={() => handleCampaignClick(campaign)}
                            >
                              {/* Campaign Preview Image - Use brand image as placeholder */}
                              <div className="flex-shrink-0">
                                <img
                                  src={brand.product_image_2_url || brand.product_image_1_url || `https://placehold.co/60x60?text=Campaign`}
                                  alt="Campaign preview"
                                  className="w-16 h-16 object-cover rounded-md bg-gray-100"
                                  onError={(e: SyntheticEvent<HTMLImageElement>) => {
                                    e.currentTarget.src = `https://placehold.co/60x60?text=Campaign`
                                  }}
                                />
                              </div>

                              {/* Campaign Info */}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  {getStatusIcon(campaign.status)}
                                  <span className="text-xs font-medium">
                                    {getStatusLabel(campaign.status)}
                                  </span>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                  {campaign.video_urls_count} scene{campaign.video_urls_count !== 1 ? 's' : ''} generated
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  Created: {new Date(campaign.created_at).toLocaleDateString()}
                                </p>
                              </div>

                              {/* Campaign Actions */}
                              <div className="flex items-center gap-2 flex-shrink-0">
                                {campaign.status === "draft" && (
                                  <GradientButton
                                    className="text-xs px-3 py-1.5"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      navigate(`/campaigns/${campaign.id}/storyline`)
                                    }}
                                  >
                                    <FileEdit className="mr-1 h-3 w-3" />
                                    Review Storyline
                                  </GradientButton>
                                )}
                                {campaign.status === "completed" && campaign.final_video_url && (
                                  <GradientButton
                                    className="text-xs px-3 py-1.5"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      navigate(`/campaigns/${campaign.id}/video`)
                                    }}
                                  >
                                    <Play className="mr-1 h-3 w-3" />
                                    View Video
                                  </GradientButton>
                                )}
                                {(campaign.status === "processing" || campaign.status === "pending") && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="text-xs"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      navigate(`/campaigns/${campaign.id}/progress`)
                                    }}
                                  >
                                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                                    View Progress
                                  </Button>
                                )}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                  onClick={(e) => handleDeleteCampaign(campaign.id, e)}
                                  disabled={deleting === campaign.id}
                                >
                                  {deleting === campaign.id ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <Trash2 className="h-4 w-4" />
                                  )}
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Empty campaigns message */}
                    {isExpanded && campaigns.length === 0 && (
                      <div className="border-t border-gray-100 bg-gray-50/50 p-6 pl-24 text-center">
                        <p className="text-sm text-muted-foreground mb-3">
                          No campaigns yet for this brand
                        </p>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigate(`/brands/${brand.id}/chat`)}
                        >
                          <Plus className="mr-2 h-3 w-3" />
                          Create First Campaign
                        </Button>
                      </div>
                    )}
                  </Card>
                )
              })}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

