import { supabase } from "./supabase"

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

/**
 * Get a valid Supabase auth token with retry logic
 */
async function getAuthToken(): Promise<string> {
  // Check localStorage for debugging
  if (typeof window !== 'undefined') {
    const storedSession = localStorage.getItem('supabase.auth.token')
    console.log('[Auth] localStorage check:', {
      hasStoredSession: !!storedSession,
      storageSize: storedSession?.length || 0
    })
  }

  // Try to get session with a small retry in case auto-refresh is in progress
  for (let attempt = 0; attempt < 3; attempt++) {
    const { data: { session }, error } = await supabase.auth.getSession()

    console.log('[Auth] getSession result (attempt ' + (attempt + 1) + '):', {
      hasSession: !!session,
      hasToken: !!session?.access_token,
      tokenExpiry: session?.expires_at ? new Date(session.expires_at * 1000).toISOString() : 'N/A',
      error: error?.message
    })

    // If we have a valid session, return it
    if (!error && session?.access_token) {
      console.log('[Auth] Valid session found')
      return session.access_token
    }

    // If first attempt fails, try manual refresh
    if (attempt === 0) {
      console.log('[Auth] Attempting manual session refresh...')
      try {
        const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession()
        console.log('[Auth] Manual refresh result:', {
          hasSession: !!refreshData.session,
          hasToken: !!refreshData.session?.access_token,
          error: refreshError?.message
        })

        if (!refreshError && refreshData.session?.access_token) {
          console.log('[Auth] Session refreshed successfully')
          return refreshData.session.access_token
        }
      } catch (refreshErr) {
        console.error('[Auth] Manual refresh failed:', refreshErr)
      }
    }

    // Wait a bit before retrying (in case auto-refresh is in progress)
    if (attempt < 2) {
      console.log('[Auth] Waiting before retry...')
      await new Promise(resolve => setTimeout(resolve, 500))
    }
  }

  console.error('[Auth] Authentication failed after all retries - no valid token')
  throw new Error('User not authenticated. Please log out and log back in.')
}

interface RequestOptions extends RequestInit {
  headers?: HeadersInit
}

async function apiRequest<T = unknown>(endpoint: string, options: RequestOptions = {}, retryCount = 0): Promise<T> {
  const maxRetries = 1
  const token = await getAuthToken()

  const url = `${API_URL}${endpoint}`

  // Add timeout to prevent hanging requests
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    })

    clearTimeout(timeoutId)

    // Handle 401 Unauthorized - might be due to invalid token
    if (response.status === 401 && retryCount < maxRetries) {
      // Try refreshing the session and retrying once
      try {
        const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession()
        if (!refreshError && refreshData.session) {
          // Retry the request with the new token
          return apiRequest<T>(endpoint, options, retryCount + 1)
        }
      } catch (refreshErr) {
        console.error("Failed to refresh session:", refreshErr)
      }
      // If refresh fails, sign out and throw error
      await supabase.auth.signOut()
      throw new Error("Session expired. Please log in again.")
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "An error occurred" })) as { detail?: string; message?: string }
      console.error(`[API] Request failed: ${response.status}`, error)
      throw new Error(error.detail || error.message || "Request failed")
    }

    const data = await response.json()
    return data as T
  } catch (error: unknown) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      console.error(`[API] Request timeout: ${url}`)
      throw new Error("Request timed out. Please check your connection.")
    }
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

    // Handle FastAPI validation errors
    if (errorData.detail && Array.isArray(errorData.detail)) {
      const errors = errorData.detail.map((e: ValidationError) => `${e.loc.join('.')}: ${e.msg}`).join(', ')
      throw new Error(errors)
    }

    throw new Error(errorData.detail as string || errorData.message || `Request failed with status ${response.status}`)
  }

  return response.json() as Promise<T>
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

  // Campaign answers
  submitCampaignAnswers: <T = unknown>(brandId: string, answers: unknown) => apiRequest<T>(`/api/brands/${brandId}/campaign-answers`, {
    method: "POST",
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
}

