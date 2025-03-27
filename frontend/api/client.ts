import axios from "axios"

const API_BASE_URL = "http://localhost:8000"

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token refresh on 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    // Only try to refresh if we have an auth token to begin with
    const hasAuthToken = localStorage.getItem("auth_token")
    
    if (error.response?.status === 401 && !originalRequest._retry && hasAuthToken) {
      originalRequest._retry = true
      try {
        // Call refresh token endpoint
        const { data } = await apiClient.post("/auth/refresh")
        // Update stored token
        localStorage.setItem("auth_token", data.session.access_token)
        // Trigger storage event for other tabs/components to detect
        window.dispatchEvent(new Event('storage'))
        // Retry the original request
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Handle refresh failure (logout, etc.)
        localStorage.removeItem("auth_token")
        // Trigger storage event for other tabs/components to detect
        window.dispatchEvent(new Event('storage'))
        // Redirect to login
        window.location.href = "/login"
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  },
)

// Add a function to manually dispatch storage event
// This helps components detect auth changes within the same window
export const notifyAuthChange = () => {
  window.dispatchEvent(new Event('storage'))
}

export default apiClient
