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
    ? "https://zapcut-ai-production.up.railway.app"
    : "http://localhost:8000"
  console.log("  ✅ Using default API URL:", apiUrl)
  console.log("  🌍 Environment:", import.meta.env.VITE_PROD ? "Production" : "Development")
  return apiUrl
}

const API_URL = getApiUrl()
console.log("🚀 Final API_URL:", API_URL)

async function getAuthToken() {
  // Skip authentication - return mock token
  return "mock-token-for-development"
}

async function apiRequest(endpoint, options = {}) {
  const token = await getAuthToken()

  console.log(`📡 API Request: ${options.method || 'GET'} ${API_URL}${endpoint}`)

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  })

  console.log(`📡 API Response: ${response.status} ${response.statusText}`)

  if (!response.ok) {
    console.error(`❌ API Error: ${response.status} ${response.statusText}`)
    console.error(`   Endpoint: ${options.method || 'GET'} ${endpoint}`)

    let errorData
    try {
      errorData = await response.json()
      console.error(`   Error details:`, errorData)
    } catch (e) {
      errorData = { detail: "An error occurred" }
      console.error(`   Could not parse error response as JSON`)
    }

    const errorMessage = errorData.detail || errorData.message || "Request failed"
    console.error(`   Error message: ${errorMessage}`)

    throw new Error(errorMessage)
  }

  const data = await response.json()
  console.log(`✅ API Success:`, data)
  return data
}

async function apiRequestWithFormData(endpoint, formData, options = {}) {
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
  getCampaigns: (brandId) => apiRequest(`/api/brands/${brandId}/campaigns`),
  getCampaign: (campaignId) => apiRequest(`/api/campaigns/${campaignId}`),
  getCampaignStatus: (campaignId) => apiRequest(`/api/campaigns/${campaignId}/status`),
  createCampaign: (data) => apiRequest("/api/campaigns", {
    method: "POST",
    body: JSON.stringify(data),
  }),
  
  // Campaign answers
  submitCampaignAnswers: (brandId, answers) => apiRequest(`/api/brands/${brandId}/campaign-answers`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  }),
  getStoryline: (brandId, creativeBibleId) => apiRequest(`/api/brands/${brandId}/storyline/${creativeBibleId}`),
}

