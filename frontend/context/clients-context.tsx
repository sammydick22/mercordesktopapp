"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import * as clientsApi from "@/api/clients"
import { useAuth } from "./auth-context"

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
  const { user, loading: authLoading } = useAuth()
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastFetchTime, setLastFetchTime] = useState<number>(0)
  const [fetchInProgress, setFetchInProgress] = useState<boolean>(false)

  // Enhanced fetch function with improved retry logic
  const fetchClients = async (retryCount = 0, force = false) => {
    // If no user or no auth token yet, don't try to fetch
    const token = localStorage.getItem("auth_token");
    if (!token && !force) {
      console.log("No auth token available yet, will retry when available");
      return;
    }
    
    // Return immediately if:
    // 1. A fetch is already in progress, OR
    // 2. It's been less than 10 seconds since the last fetch AND force is false AND we have data
    const now = Date.now();
    const timeSinceLastFetch = now - lastFetchTime;
    
    if (fetchInProgress) {
      console.log("Fetch already in progress, skipping");
      return;
    }
    
    if (!force && timeSinceLastFetch < 10000 && clients.length > 0) {
      console.log("Using cached clients data");
      return;
    }
    
    setFetchInProgress(true);
    setLoading(true);
    setError(null);
    
    try {
      console.log("Fetching clients...");
      const { data } = await clientsApi.getClients();
      console.log("Clients fetched:", data);
      setLastFetchTime(Date.now());
      
      // Handle both possible response formats
      if (data.clients) {
        setClients(data.clients);
      } else if (Array.isArray(data)) {
        setClients(data);
      } else {
        console.warn("Unexpected clients response format:", data);
        setClients([]);
      }
    } catch (err: any) {
      console.error("Error fetching clients:", err);
      setError(err.response?.data?.message || "Failed to fetch clients");
      
      // Enhanced retry logic with increasing delays
      if (retryCount < 5) { // Increase max retries from 3 to 5
        // Calculate delay with exponential backoff (1s, 2s, 4s, 8s, 16s)
        const delay = Math.min(1000 * Math.pow(2, retryCount), 16000);
        console.log(`Retrying clients fetch (${retryCount + 1}/5) in ${delay}ms...`);
        setTimeout(() => fetchClients(retryCount + 1, force), delay);
        return;
      }
    } finally {
      setLoading(false);
      setFetchInProgress(false);
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

  // Initial fetch effect - only runs once on mount
  useEffect(() => {
    fetchClients()
  }, [])
  
  // Add effect to fetch again when auth status changes
  useEffect(() => {
    // Listen for auth token changes
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === "auth_token" && event.newValue) {
        console.log("Auth token changed, fetching clients");
        fetchClients(0, true); // Force refresh with retryCount=0
      }
    };
    
    // Listen for storage events (when token is added/removed in other tabs)
    window.addEventListener('storage', handleStorageChange);
    
    // Also listen for the custom storage event we dispatch within the same window
    window.addEventListener('storage', () => {
      console.log("Internal storage event, checking clients");
      const token = localStorage.getItem("auth_token");
      if (token && clients.length === 0) {
        console.log("Auth token available but no clients, fetching");
        fetchClients(0, true);
      }
    });
    
    // Return cleanup function
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [clients.length]);
  
  // Also fetch when user changes (after login/logout)
  useEffect(() => {
    if (user && !authLoading) {
      console.log("User authenticated, fetching clients");
      fetchClients(0, true);
    }
  }, [user, authLoading]);

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
