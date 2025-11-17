import { supabase } from "./supabase"

// API Configuration - HTTPS in production, HTTP in development
const getApiUrl = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL as string
  }
  const apiUrl = import.meta.env.VITE_PROD
    ? "https://zapcut-api.fly.dev"
    : "http://localhost:8000"
  return apiUrl
}

const API_URL = getApiUrl()

/**
 * Get a valid Supabase auth token
 */
async function getAuthToken(): Promise<string> {
  let { data: { session }, error } = await supabase.auth.getSession()

  // If no session or error, try to refresh
  if (error || !session?.access_token) {
    try {
      const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession()
      if (!refreshError && refreshData.session?.access_token) {
        return refreshData.session.access_token
      }
    } catch (refreshErr) {
      console.error('Failed to refresh session:', refreshErr)
    }
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

