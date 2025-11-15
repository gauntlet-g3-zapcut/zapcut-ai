import { auth } from "./firebase"

// API Configuration - HTTPS in production, HTTP in development
const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  return import.meta.env.PROD 
    ? "https://adcraft-production.up.railway.app" 
    : "http://localhost:8000"
}

const API_URL = getApiUrl()

async function getAuthToken() {
  const user = auth.currentUser
  if (!user) {
    throw new Error("User not authenticated")
  }
  return await user.getIdToken()
}

async function apiRequest(endpoint, options = {}) {
  const token = await getAuthToken()
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "An error occurred" }))
    throw new Error(error.detail || error.message || "Request failed")
  }

  return response.json()
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

