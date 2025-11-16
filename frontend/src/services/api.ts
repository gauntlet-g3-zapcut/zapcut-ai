import { supabase } from "./supabase"

// API Configuration - HTTPS in production, HTTP in development
const getApiUrl = () => {
  console.log("🔧 API Configuration:")
  console.log("  VITE_API_URL:", import.meta.env.VITE_API_URL)
  console.log("  VITE_PROD:", import.meta.env.VITE_PROD)

  if (import.meta.env.VITE_API_URL) {
    console.log("  ✅ Using VITE_API_URL:", import.meta.env.VITE_API_URL)
    return import.meta.env.VITE_API_URL
  }
  const apiUrl = import.meta.env.VITE_PROD
    ? "https://zapcut-api.fly.dev"
    : "http://localhost:8000"
  console.log("  ✅ Using default API URL:", apiUrl)
  console.log("  🌍 Environment:", import.meta.env.VITE_PROD ? "Production" : "Development")
  return apiUrl
}

const API_URL = getApiUrl()
console.log("🚀 Final API_URL:", API_URL)

/**
 * Get a valid Supabase auth token
 */
async function getAuthToken(): Promise<string> {
  const { data: { session }, error } = await supabase.auth.getSession()

  if (error || !session?.access_token) {
    throw new Error('User not authenticated')
  }

  return session.access_token
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

async function apiRequestWithFormData<T = unknown>(endpoint: string, formData: FormData, options: RequestOptions = {}, retryCount = 0): Promise<T> {
  const maxRetries = 1
  const token = await getAuthToken()

  const response = await fetch(`${API_URL}${endpoint}`, {
    method: "POST",
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
    let errorData
    try {
      errorData = await response.json()
    } catch {
      errorData = { detail: `Request failed with status ${response.status}` }
    }

    // Handle FastAPI validation errors
    if (errorData.detail && Array.isArray(errorData.detail)) {
      const errors = errorData.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ')
      throw new Error(errors)
    }

    throw new Error(errorData.detail || errorData.message || `Request failed with status ${response.status}`)
  }

  return response.json()
}

export const api = {
  // Brands
  getBrands: () => apiRequest("/api/brands/"),
  getBrand: (brandId) => apiRequest(`/api/brands/${brandId}`),
  createBrand: (formData) => apiRequestWithFormData("/api/brands/", formData),
  createCreativeBible: (brandId, answers) => apiRequest(`/api/brands/${brandId}/creative-bible`, {
    method: "POST",
    body: JSON.stringify({ answers }),
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
  submitCampaignAnswers: (brandId, answers) => apiRequest(`/api/brands/${brandId}/campaign-answers`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  }),
  getStoryline: (brandId, creativeBibleId) => apiRequest(`/api/brands/${brandId}/storyline/${creativeBibleId}`),
}

