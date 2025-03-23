import apiClient from "./client"

export const startTimeEntry = (projectId?: string, taskId?: string, description?: string) =>
  apiClient.post("/time-entries/start", { project_id: projectId, task_id: taskId, description })

export const stopTimeEntry = (description?: string) => apiClient.post("/time-entries/stop", { description })

export const getCurrentTimeEntry = () => apiClient.get("/time-entries/current")

export const getTimeEntries = (limit = 10, offset = 0) => apiClient.get("/time-entries", { params: { limit, offset } })

