import apiClient from "./client"

export const syncAll = () => apiClient.post("/sync/all")

export const syncActivities = () => apiClient.post("/sync/activities")

export const syncScreenshots = () => apiClient.post("/sync/screenshots")

export const syncOrganization = () => apiClient.post("/sync/organization")

export const getSyncStatus = () => apiClient.get("/sync/status")

export const startBackgroundSync = () => apiClient.post("/sync/background")

