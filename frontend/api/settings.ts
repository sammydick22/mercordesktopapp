import apiClient from "./client"

export const getSettings = () => apiClient.get("/settings")

export const resetSettings = () => apiClient.get("/settings/reset")

export const updateSettings = (data: {
  screenshot_interval?: number
  screenshot_quality?: "low" | "medium" | "high"
  auto_sync_interval?: number
  idle_detection_timeout?: number
  theme?: "light" | "dark" | "system"
  notifications_enabled?: boolean
}) => apiClient.put("/settings", data)

export const setActiveOrganization = (orgId: string) => 
  apiClient.put("/settings/active-organization", { organization_id: orgId })

export const getUserProfile = () => apiClient.get("/profile")

export const updateUserProfile = (data: {
  name?: string
  email?: string
  timezone?: string
  hourly_rate?: number
  avatar_url?: string
}) => apiClient.put("/profile", data)

export const changePassword = (data: {
  current_password: string
  new_password: string
}) => apiClient.post("/auth/change-password", data)
