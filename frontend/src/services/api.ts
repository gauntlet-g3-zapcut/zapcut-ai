import { supabase, DEBUG_AUTH } from "./supabase"
import type { CampaignAnswers } from "../types/campaign"
import type { ImageMetadata, ImageUploadResponse, UpdateImageMetadataRequest, ReorderImagesRequest } from "../types/image"

// API Configuration - HTTPS in production, HTTP in development
const getApiUrl = (): string => {
  // if (import.meta.env.VITE_API_URL) {
  //   return import.meta.env.VITE_API_URL as string
  // }
  const apiUrl = import.meta.env.VITE_PROD === 'true'
    ? "https://zapcut-api.fly.dev"
    : "http://localhost:8000"
  return apiUrl
}

const API_URL = getApiUrl()

// Log production API URL for visibility
if (import.meta.env.VITE_PROD === 'true') {
  console.log('🚀 PRODUCTION MODE - API URL:', API_URL)
} else {
  console.log('🔧 DEVELOPMENT MODE - API URL:', API_URL)
}
const TOKEN_REFRESH_BUFFER_MS = 60_000

// Helper for conditional logging
const debugLog = (...args: unknown[]) => {
  if (DEBUG_AUTH) {
    console.log(...args)
  }
}

/**
 * Get a valid Supabase auth token with retry logic
 */
const shouldRefreshSession = (session: { expires_at?: number } | null): boolean => {
  if (!session?.expires_at) return false
  return session.expires_at * 1000 - Date.now() <= TOKEN_REFRESH_BUFFER_MS
}

async function getAuthToken(): Promise<string> {
  // Check localStorage for debugging
  if (typeof window !== 'undefined') {
    const storedSession = localStorage.getItem('supabase.auth.token')
    debugLog('[Auth] localStorage check:', {
      hasStoredSession: !!storedSession,
      storageSize: storedSession?.length || 0
    })
  }

  // Try to get session with a small retry in case auto-refresh is in progress
  for (let attempt = 0; attempt < 3; attempt++) {
    const { data: { session }, error } = await supabase.auth.getSession()

    debugLog('[Auth] getSession result (attempt ' + (attempt + 1) + '):', {
      hasSession: !!session,
      hasToken: !!session?.access_token,
      tokenExpiry: session?.expires_at ? new Date(session.expires_at * 1000).toISOString() : 'N/A',
      error: error?.message
    })

    // If we have a valid session, return it
    if (!error && session?.access_token) {
      if (shouldRefreshSession(session)) {
        debugLog('[Auth] Session expiring soon; attempting proactive refresh')
        try {
          const { data: refreshed, error: refreshError } = await supabase.auth.refreshSession()
          if (!refreshError && refreshed.session?.access_token) {
            debugLog('[Auth] Session refreshed proactively')
            return refreshed.session.access_token
          }
          if (refreshError) {
            console.error('[Auth] Proactive refresh failed:', refreshError)
          }
        } catch (refreshErr) {
          console.error('[Auth] Proactive refresh exception:', refreshErr)
        }
      } else {
        debugLog('[Auth] Valid session found')
        return session.access_token
      }
    }

    if (!error && session?.access_token) {
      return session.access_token
    }

    // If first attempt fails, try manual refresh
    if (attempt === 0) {
      debugLog('[Auth] Attempting manual session refresh...')
      try {
        const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession()
        debugLog('[Auth] Manual refresh result:', {
          hasSession: !!refreshData.session,
          hasToken: !!refreshData.session?.access_token,
          error: refreshError?.message
        })

        if (!refreshError && refreshData.session?.access_token) {
          debugLog('[Auth] Session refreshed successfully')
          return refreshData.session.access_token
        }
      } catch (refreshErr) {
        if (DEBUG_AUTH) {
          console.error('[Auth] Manual refresh failed:', refreshErr)
        }
      }
    }

    // Wait a bit before retrying (in case auto-refresh is in progress)
    if (attempt < 2) {
      debugLog('[Auth] Waiting before retry...')
      await new Promise(resolve => setTimeout(resolve, 500))
    }
  }

  if (DEBUG_AUTH) {
    console.error('[Auth] Authentication failed after all retries - no valid token')
  }
  throw new Error('User not authenticated. Please log out and log back in.')
}

interface RequestOptions extends RequestInit {
  headers?: HeadersInit
}

async function apiRequest<T = unknown>(endpoint: string, options: RequestOptions = {}, retryCount = 0): Promise<T> {
  const maxRetries = 1
  const requestId = Math.random().toString(36).substring(7)

  if (DEBUG_AUTH) {
    console.log(`[API:${requestId}] ⏳ Starting request:`, {
      endpoint,
      method: options.method || 'GET',
      hasBody: !!options.body,
      retryCount,
      timestamp: new Date().toISOString(),
    })
  }

  const token = await getAuthToken()
  if (DEBUG_AUTH) console.log(`[API:${requestId}] ✅ Got auth token (length: ${token.length})`)

  const url = `${API_URL}${endpoint}`
  if (DEBUG_AUTH) console.log(`[API:${requestId}] 🌐 Full URL: ${url}`)

  // Add timeout to prevent hanging requests
  const controller = new AbortController()
  const timeoutId = setTimeout(() => {
    console.error(`[API:${requestId}] ⏰ Request timeout after 30s`)
    controller.abort()
  }, 30000) // 30 second timeout

  try {
    if (DEBUG_AUTH) console.log(`[API:${requestId}] 📡 Sending fetch request...`)
    const fetchStartTime = Date.now()

    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    })

    const fetchDuration = Date.now() - fetchStartTime
    if (DEBUG_AUTH) {
      console.log(`[API:${requestId}] 📥 Response received (${fetchDuration}ms):`, {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
      })
    }

    clearTimeout(timeoutId)

    // Handle 401 Unauthorized - might be due to invalid token
    if (response.status === 401 && retryCount < maxRetries) {
      if (DEBUG_AUTH) console.log(`[API:${requestId}] 🔄 Got 401, attempting to refresh session...`)
      // Try refreshing the session and retrying once
      try {
        const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession()
        if (!refreshError && refreshData.session) {
          if (DEBUG_AUTH) console.log(`[API:${requestId}] ✅ Session refreshed, retrying request...`)
          // Retry the request with the new token
          return apiRequest<T>(endpoint, options, retryCount + 1)
        }
        console.error(`[API:${requestId}] ❌ Session refresh failed:`, refreshError)
      } catch (refreshErr) {
        console.error(`[API:${requestId}] ❌ Exception during session refresh:`, refreshErr)
      }
      // If refresh fails, sign out and throw error
      if (DEBUG_AUTH) console.log(`[API:${requestId}] 🚪 Signing out due to auth failure`)
      await supabase.auth.signOut()
      throw new Error("Session expired. Please log in again.")
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "An error occurred" })) as { detail?: string; message?: string }
      console.error(`[API:${requestId}] ❌ Request failed:`, {
        endpoint,
        status: response.status,
        statusText: response.statusText,
        error,
      })
      throw new Error(error.detail || error.message || "Request failed")
    }

    if (DEBUG_AUTH) console.log(`[API:${requestId}] 📦 Parsing JSON response...`)
    const data = await response.json()
    if (DEBUG_AUTH) {
      console.log(`[API:${requestId}] ✅ Request successful:`, {
        endpoint,
        status: response.status,
        dataKeys: typeof data === 'object' && data !== null ? Object.keys(data) : 'non-object',
        isArray: Array.isArray(data),
        arrayLength: Array.isArray(data) ? data.length : undefined,
        totalDuration: `${Date.now() - fetchStartTime}ms`,
      })
    }
    return data as T
  } catch (error: unknown) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      console.error(`[API:${requestId}] ⏰ Request timeout: ${url}`)
      throw new Error("Request timed out. Please check your connection.")
    }
    console.error(`[API:${requestId}] 💥 Request failed with error:`, error)
    throw error
  }
}

interface FormDataRequestOptions extends RequestInit {
  headers?: HeadersInit
}

interface ValidationError {
  loc: (string | number)[]
  msg: string
}

async function apiRequestWithFormData<T = unknown>(endpoint: string, formData: FormData, options: FormDataRequestOptions = {}, retryCount = 0): Promise<T> {
  const maxRetries = 1
  const token = await getAuthToken()

  // Log FormData contents for debugging
  debugLog('[API] FormData request starting:', {
    endpoint,
    method: options.method || "POST",
    formDataKeys: Array.from(formData.keys()),
  })

  // Log file details
  if (DEBUG_AUTH) {
    formData.forEach((value, key) => {
      if (value instanceof File) {
        console.log(`[API] FormData file: ${key}`, {
          name: value.name,
          size: value.size,
          type: value.type,
        })
      } else {
        console.log(`[API] FormData field: ${key} =`, value)
      }
    })
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    method: options.method || "POST",
    body: formData,
    headers: {
      Authorization: `Bearer ${token}`,
      // Don't set Content-Type - browser will set it with boundary for FormData
      ...options.headers,
    },
  })

  // Handle 401 Unauthorized - might be due to invalid token
  if (response.status === 401 && retryCount < maxRetries) {
    // Try refreshing the session and retrying once
    try {
      const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession()
      if (!refreshError && refreshData.session) {
        // Retry the request with the new token
        return apiRequestWithFormData<T>(endpoint, formData, options, retryCount + 1)
      }
    } catch (refreshErr) {
      console.error("Failed to refresh session:", refreshErr)
    }
    // If refresh fails, sign out and throw error
    await supabase.auth.signOut()
    throw new Error("Session expired. Please log in again.")
  }

  if (!response.ok) {
    let errorData: { detail?: string | ValidationError[]; message?: string }
    try {
      errorData = await response.json()
    } catch {
      errorData = { detail: `Request failed with status ${response.status}` }
    }

    console.error('[API] FormData request failed:', {
      endpoint,
      status: response.status,
      statusText: response.statusText,
      error: errorData,
    })

    // Handle FastAPI validation errors
    if (errorData.detail && Array.isArray(errorData.detail)) {
      const errors = errorData.detail.map((e: ValidationError) => `${e.loc.join('.')}: ${e.msg}`).join(', ')
      throw new Error(errors)
    }

    throw new Error(errorData.detail as string || errorData.message || `Request failed with status ${response.status}`)
  }

  const responseData = await response.json() as Promise<T>
  debugLog('[API] FormData request successful:', {
    endpoint,
    status: response.status,
    data: responseData,
  })

  return responseData
}

export const api = {
  // Brands
  getBrands: <T = unknown>() => apiRequest<T>("/api/brands/"),
  getBrand: <T = unknown>(brandId: string) => apiRequest<T>(`/api/brands/${brandId}`),
  createBrand: <T = unknown>(formData: FormData) => apiRequestWithFormData<T>("/api/brands/", formData),
  updateBrand: <T = unknown>(brandId: string, formData: FormData) => apiRequestWithFormData<T>(`/api/brands/${brandId}`, formData, {
    method: "PUT",
  }),
  deleteBrand: <T = unknown>(brandId: string) => apiRequest<T>(`/api/brands/${brandId}`, {
    method: "DELETE",
  }),

  // Campaigns
  getAllCampaigns: <T = unknown>() => apiRequest<T>("/api/campaigns/"),
  getCampaigns: <T = unknown>(brandId: string) => apiRequest<T>(`/api/brands/${brandId}/campaigns`),
  getCampaign: <T = unknown>(campaignId: string) => apiRequest<T>(`/api/campaigns/${campaignId}`),
  getCampaignStatus: <T = unknown>(campaignId: string) => apiRequest<T>(`/api/campaigns/${campaignId}/status`),
  createCampaign: <T = unknown>(data: unknown) => apiRequest<T>("/api/campaigns/", {
    method: "POST",
    body: JSON.stringify(data),
  }),
  deleteCampaign: <T = unknown>(campaignId: string) => apiRequest<T>(`/api/campaigns/${campaignId}`, {
    method: "DELETE",
  }),
  approveCampaign: <T = unknown>(campaignId: string) => apiRequest<T>(`/api/campaigns/${campaignId}/approve`, {
    method: "POST",
  }),

  // Campaign answers
  submitCampaignAnswers: <T = unknown>(brandId: string, answers: CampaignAnswers) => apiRequest<T>(`/api/brands/${brandId}/campaign-answers`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  }),
  updateCampaignAnswers: <T = unknown>(brandId: string, creativeBibleId: string, answers: CampaignAnswers) => apiRequest<T>(`/api/brands/${brandId}/campaign-answers/${creativeBibleId}`, {
    method: "PUT",
    body: JSON.stringify({ answers }),
  }),
  getStoryline: <T = unknown>(brandId: string, creativeBibleId: string) => apiRequest<T>(`/api/brands/${brandId}/storyline/${creativeBibleId}`),

  // Chat
  createChatSession: <T = unknown>(brandId: string) => apiRequest<T>(`/api/brands/${brandId}/chat-session`, {
    method: "POST",
  }),
  getChatSession: <T = unknown>(brandId: string, creativeBibleId: string) => apiRequest<T>(`/api/brands/${brandId}/chat-session/${creativeBibleId}`),
  sendChatMessage: <T = unknown>(brandId: string, creativeBibleId: string, message: string) => apiRequest<T>(`/api/brands/${brandId}/chat/${creativeBibleId}`, {
    method: "POST",
    body: JSON.stringify({ message }),
  }),
  getChatMessages: <T = unknown>(brandId: string, creativeBibleId: string) => apiRequest<T>(`/api/brands/${brandId}/chat/${creativeBibleId}/messages`),
  completeChat: <T = unknown>(brandId: string, creativeBibleId: string) => apiRequest<T>(`/api/brands/${brandId}/chat/${creativeBibleId}/complete`, {
    method: "POST",
  }),

  // Storyline editing
  updateStoryline: <T = unknown>(brandId: string, creativeBibleId: string, sceneNumber: number, description: string) => apiRequest<T>(`/api/brands/${brandId}/storyline/${creativeBibleId}`, {
    method: "PUT",
    body: JSON.stringify({ scene_number: sceneNumber, description }),
  }),
  revertStoryline: <T = unknown>(brandId: string, creativeBibleId: string) => apiRequest<T>(`/api/brands/${brandId}/storyline/${creativeBibleId}/revert`, {
    method: "POST",
  }),

  // Brand Images
  uploadBrandImages: async (brandId: string, images: File[]): Promise<ImageUploadResponse> => {
    const formData = new FormData();
    images.forEach((image) => {
      formData.append('images', image);
    });

    const token = await getAuthToken();
    const response = await fetch(`${API_URL}/api/brands/${brandId}/images`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload images');
    }

    return response.json();
  },

  deleteBrandImage: <T = unknown>(brandId: string, imageId: string) => apiRequest<T>(`/api/brands/${brandId}/images/${imageId}`, {
    method: "DELETE",
  }),

  updateBrandImage: (brandId: string, imageId: string, data: UpdateImageMetadataRequest) =>
    apiRequest<ImageMetadata>(`/api/brands/${brandId}/images/${imageId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  reorderBrandImages: (brandId: string, imageIds: string[]) =>
    apiRequest<{ message: string; images: ImageMetadata[] }>(`/api/brands/${brandId}/images/reorder`, {
      method: "PUT",
      body: JSON.stringify({ image_ids: imageIds }),
    }),

  // Campaign Images
  getCampaignImages: <T = unknown>(campaignId: string) => apiRequest<T>(`/api/campaigns/${campaignId}/images`),

  uploadCampaignImages: async (campaignId: string, images: File[]): Promise<ImageUploadResponse> => {
    const formData = new FormData();
    images.forEach((image) => {
      formData.append('images', image);
    });

    const token = await getAuthToken();
    const response = await fetch(`${API_URL}/api/campaigns/${campaignId}/images`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload images');
    }

    return response.json();
  },

  deleteCampaignImage: <T = unknown>(campaignId: string, imageId: string) => apiRequest<T>(`/api/campaigns/${campaignId}/images/${imageId}`, {
    method: "DELETE",
  }),

  updateCampaignImage: (campaignId: string, imageId: string, data: UpdateImageMetadataRequest) =>
    apiRequest<ImageMetadata>(`/api/campaigns/${campaignId}/images/${imageId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  reorderCampaignImages: (campaignId: string, imageIds: string[]) =>
    apiRequest<{ message: string; images: ImageMetadata[] }>(`/api/campaigns/${campaignId}/images/reorder`, {
      method: "PUT",
      body: JSON.stringify({ image_ids: imageIds }),
    }),
}

