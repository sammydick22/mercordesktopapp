import apiClient from "./client"

export const getProjects = (limit = 50, offset = 0) => apiClient.get("/projects", { params: { limit, offset } })

export const getProject = (id: string) => apiClient.get(`/projects/${id}`)

export const createProject = (data: {
  name: string
  client_id?: string
  description?: string
  color?: string
  hourly_rate?: number
  is_billable?: boolean
}) => apiClient.post("/projects", data)

export const updateProject = (
  id: string,
  data: {
    name?: string
    client_id?: string
    description?: string
    color?: string
    hourly_rate?: number
    is_billable?: boolean
    is_active?: boolean
  },
) => apiClient.put(`/projects/${id}`, data)

export const deleteProject = (id: string) => apiClient.delete(`/projects/${id}`)

export const getProjectTasks = (projectId: string, limit = 50, offset = 0) =>
  apiClient.get(`/projects/${projectId}/tasks`, { params: { limit, offset } })

export const createProjectTask = (
  projectId: string,
  data: {
    name: string
    description?: string
    estimated_hours?: number
  },
) => apiClient.post(`/projects/${projectId}/tasks`, data)

export const updateProjectTask = (
  projectId: string,
  taskId: string,
  data: {
    name?: string
    description?: string
    estimated_hours?: number
    is_active?: boolean
  },
) => apiClient.put(`/projects/${projectId}/tasks/${taskId}`, data)

export const deleteProjectTask = (projectId: string, taskId: string) =>
  apiClient.delete(`/projects/${projectId}/tasks/${taskId}`)

