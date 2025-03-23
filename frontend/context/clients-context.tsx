"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import * as clientsApi from "@/api/clients"

interface Client {
  id: string
  name: string
  contact_name?: string
  email?: string
  phone?: string
  address?: string
  notes?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface ClientsContextType {
  clients: Client[]
  activeClients: Client[]
  loading: boolean
  error: string | null
  fetchClients: () => Promise<void>
  getClient: (id: string) => Promise<Client>
  createClient: (data: {
    name: string
    contact_name?: string
    email?: string
    phone?: string
    address?: string
    notes?: string
  }) => Promise<Client>
  updateClient: (
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
  ) => Promise<Client>
  deleteClient: (id: string) => Promise<void>
}

const ClientsContext = createContext<ClientsContextType | undefined>(undefined)

export function ClientsProvider({ children }: { children: ReactNode }) {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchClients = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await clientsApi.getClients()
      setClients(data.clients || [])
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to fetch clients")
      console.error("Error fetching clients:", err)
    } finally {
      setLoading(false)
    }
  }

  const getClient = async (id: string): Promise<Client> => {
    try {
      const { data } = await clientsApi.getClient(id)
      return data.client
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to fetch client")
    }
  }

  const createClient = async (clientData: {
    name: string
    contact_name?: string
    email?: string
    phone?: string
    address?: string
    notes?: string
  }): Promise<Client> => {
    try {
      const { data } = await clientsApi.createClient(clientData)
      setClients((prev) => [...prev, data.client])
      return data.client
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to create client")
    }
  }

  const updateClient = async (
    id: string,
    clientData: {
      name?: string
      contact_name?: string
      email?: string
      phone?: string
      address?: string
      notes?: string
      is_active?: boolean
    },
  ): Promise<Client> => {
    try {
      const { data } = await clientsApi.updateClient(id, clientData)
      setClients((prev) => prev.map((client) => (client.id === id ? data.client : client)))
      return data.client
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to update client")
    }
  }

  const deleteClient = async (id: string): Promise<void> => {
    try {
      await clientsApi.deleteClient(id)
      setClients((prev) => prev.filter((client) => client.id !== id))
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to delete client")
    }
  }

  useEffect(() => {
    fetchClients()
  }, [])

  const activeClients = clients.filter((client) => client.is_active)

  return (
    <ClientsContext.Provider
      value={{
        clients,
        activeClients,
        loading,
        error,
        fetchClients,
        getClient,
        createClient,
        updateClient,
        deleteClient,
      }}
    >
      {children}
    </ClientsContext.Provider>
  )
}

export function useClients() {
  const context = useContext(ClientsContext)
  if (context === undefined) {
    throw new Error("useClients must be used within a ClientsProvider")
  }
  return context
}

