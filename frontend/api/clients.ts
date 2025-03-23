import apiClient from "./client"

export const getClients = (limit = 50, offset = 0) => apiClient.get("/clients", { params: { limit, offset } })

export const getClient = (id: string) => apiClient.get(`/clients/${id}`)

export const createClient = (data: {
  name: string
  contact_name?: string
  email?: string
  phone?: string
  address?: string
  notes?: string
}) => apiClient.post("/clients", data)

export const updateClient = (
  id: string,
  data: {
    name?: string
    contact_name?: string
    email?: string
    phone?: string
    address?: string
    notes?: string
    is_active?: boolean
  },
) => apiClient.put(`/clients/${id}`, data)

export const deleteClient = (id: string) => apiClient.delete(`/clients/${id}`)

