import { supabase } from "./supabase"

// API Configuration - HTTPS in production, HTTP in development
const getApiUrl = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL as string
  }
  const apiUrl = import.meta.env.VITE_PROD
    ? "https://zapcut-ai-production.up.railway.app"
    : "http://localhost:8000"
  console.log("API URL:", apiUrl)
  return apiUrl
}

const API_URL = getApiUrl()

/**
 * Decode JWT header to check algorithm without verification
 */
function getTokenAlgorithm(token: string): string | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const header = JSON.parse(atob(parts[0].replace(/-/g, '+').replace(/_/g, '/')))
    return header.alg
  } catch (e) {
    return null
  }
}

/**
 * Get a valid Supabase auth token, refreshing if necessary
 * Supabase tokens should always use RS256 algorithm
 */
async function getAuthToken() {
  // First, try to get the current session
  let { data: { session }, error } = await supabase.auth.getSession()

  if (error || !session) {
    throw new Error("User not authenticated")
  }

  // Check if the token has the correct algorithm (Supabase uses RS256)
  const tokenAlgorithm = getTokenAlgorithm(session.access_token)
  
  if (tokenAlgorithm && tokenAlgorithm !== "RS256") {
    console.warn(`Invalid token algorithm detected: ${tokenAlgorithm}. Expected RS256. Clearing invalid session...`)
    
    // If we have a non-RS256 token, it's likely corrupted or from a different source
    // Clear the session immediately and force re-authentication
    await supabase.auth.signOut()
    
    // Clear localStorage to remove any stale tokens
    if (typeof window !== 'undefined') {
      const keys = Object.keys(localStorage)
      keys.forEach(key => {
        if (key.includes('supabase') || key.includes('auth')) {
          localStorage.removeItem(key)
        }
      })
    }
    
    throw new Error(`Invalid token algorithm: ${tokenAlgorithm}. Supabase uses RS256. Please log in again.`)
  }

  // Verify the token is from the correct Supabase project
  try {
    const tokenParts = session.access_token.split('.')
    if (tokenParts.length === 3) {
      const payload = JSON.parse(atob(tokenParts[1].replace(/-/g, '+').replace(/_/g, '/')))
      const issuer = payload.iss
      
      // Verify issuer is from Supabase (should contain supabase.co or supabase.io)
      if (issuer && !issuer.includes('supabase.co') && !issuer.includes('supabase.io')) {
        console.warn(`Token issuer mismatch. Expected Supabase issuer, got: ${issuer}`)
        await supabase.auth.signOut()
        throw new Error("Invalid token issuer. Please log in again.")
      }
    }
  } catch (e) {
    // If we can't verify the token structure, it's invalid
    if (e instanceof Error && e.message.includes("Invalid token issuer")) {
      throw e // Re-throw issuer errors
    }
    console.error("Failed to verify token structure:", e)
    await supabase.auth.signOut()
    throw new Error("Invalid token format. Please log in again.")
  }

  return session.access_token
}

interface RequestOptions extends RequestInit {
  headers?: HeadersInit
}

async function apiRequest<T = unknown>(endpoint: string, options: RequestOptions = {}, retryCount = 0): Promise<T> {
  const maxRetries = 1
  const token = await getAuthToken()

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  })

  // Handle 401 Unauthorized - might be due to invalid token
  if (response.status === 401 && retryCount < maxRetries) {
    // Try refreshing the session and retrying once
    console.warn("Received 401, attempting to refresh session and retry...")
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
    throw new Error(error.detail || error.message || "Request failed")
  }

  return response.json() as Promise<T>
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
    console.warn("Received 401, attempting to refresh session and retry...")
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

  // Campaigns
  getCampaigns: <T = unknown>(brandId: string) => apiRequest<T>(`/api/brands/${brandId}/campaigns`),
  getCampaign: <T = unknown>(campaignId: string) => apiRequest<T>(`/api/campaigns/${campaignId}`),
  getCampaignStatus: <T = unknown>(campaignId: string) => apiRequest<T>(`/api/campaigns/${campaignId}/status`),
  createCampaign: <T = unknown>(data: unknown) => apiRequest<T>("/api/campaigns", {
    method: "POST",
    body: JSON.stringify(data),
  }),

  // Campaign answers
  submitCampaignAnswers: <T = unknown>(brandId: string, answers: unknown) => apiRequest<T>(`/api/brands/${brandId}/campaign-answers`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  }),
  getStoryline: <T = unknown>(brandId: string, creativeBibleId: string) => apiRequest<T>(`/api/brands/${brandId}/storyline/${creativeBibleId}`),
}

