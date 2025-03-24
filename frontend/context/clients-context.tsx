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

  // Enhanced fetch function with global throttling, caching and retry logic
  const fetchClients = async (retryCount = 0, force = false) => {
    // If no user or no auth token yet, don't try to fetch
    const token = localStorage.getItem("auth_token");
    if (!token && !force) {
      console.log("No auth token available yet, will retry when available");
      return;
    }
    
    // GLOBAL THROTTLING: Use localStorage to share state between multiple component instances
    const now = Date.now();
    const globalLastFetchTime = parseInt(localStorage.getItem("clients_global_last_fetch") || "0");
    const globalFetchInProgress = localStorage.getItem("clients_fetch_in_progress") === "true";
    const timeSinceLastFetch = now - globalLastFetchTime;
    
    // Use cached data from localStorage if available
    const cachedData = localStorage.getItem("clients_cached_data");
    if (cachedData && !force && clients.length === 0) {
      try {
        const parsed = JSON.parse(cachedData);
        
        // Check if we actually need to update state to avoid re-render loops
        // Only set state if clients is empty and parsed data isn't
        if (clients.length === 0 && parsed.length > 0) {
          console.log("Using clients data from localStorage cache");
          setClients(parsed);
        } else {
          console.log("Using cached data without state update");
        }
      } catch (e) {
        console.error("Error parsing cached clients data:", e);
      }
    }
    
    // Return immediately if:
    // 1. A fetch is already in progress globally, OR
    // 2. It's been less than 30 seconds since the last fetch AND force is false AND we have data
    if (globalFetchInProgress) {
      console.log("Clients fetch already in progress globally, skipping");
      return;
    }
    
    if (!force && timeSinceLastFetch < 30000 && (clients.length > 0 || cachedData)) {
      console.log(`Using cached clients data (last fetch: ${timeSinceLastFetch/1000}s ago)`);
      return;
    }
    
    // Set global in-progress flag
    localStorage.setItem("clients_fetch_in_progress", "true");
    setFetchInProgress(true);
    setLoading(true);
    setError(null);
    
    try {
      console.log("Fetching clients...");
      const { data } = await clientsApi.getClients();
      console.log("Clients fetched:", data);
      
      // Update global last fetch time
      const fetchTime = Date.now();
      localStorage.setItem("clients_global_last_fetch", fetchTime.toString());
      setLastFetchTime(fetchTime);
      
      // Handle both possible response formats
      let clientsData = [];
      if (data.clients) {
        clientsData = data.clients;
      } else if (Array.isArray(data)) {
        clientsData = data;
      } else {
        console.warn("Unexpected clients response format:", data);
      }
      
      // Save to local state
      setClients(clientsData);
      
      // Cache data in localStorage
      try {
        localStorage.setItem("clients_cached_data", JSON.stringify(clientsData));
      } catch (e) {
        console.warn("Failed to cache clients in localStorage:", e);
      }
    } catch (err: any) {
      console.error("Error fetching clients:", err);
      setError(err.response?.data?.message || "Failed to fetch clients");
      
      // Enhanced retry logic with increasing delays
      if (retryCount < 3) { // Reduced retry count
        // Calculate delay with exponential backoff (1s, 2s, 4s)
        const delay = Math.min(1000 * Math.pow(2, retryCount), 4000);
        console.log(`Retrying clients fetch (${retryCount + 1}/3) in ${delay}ms...`);
        setTimeout(() => fetchClients(retryCount + 1, force), delay);
        return;
      }
    } finally {
      setLoading(false);
      setFetchInProgress(false);
      localStorage.setItem("clients_fetch_in_progress", "false");
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

  // Clear in-progress flag on unmount to prevent deadlocks
  useEffect(() => {
    return () => {
      localStorage.setItem("clients_fetch_in_progress", "false");
    };
  }, []);

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
    
    // Listen for global fetch completed events
    const handleFetchComplete = (event: StorageEvent) => {
      if (event.key === "clients_global_last_fetch" && event.newValue) {
        // Another instance has completed a fetch, we should check our local state
        const cachedData = localStorage.getItem("clients_cached_data");
        if (cachedData && clients.length === 0) {
          try {
            const parsedData = JSON.parse(cachedData);
            // Only update state if there's actual data and our current state is empty
            if (parsedData && parsedData.length > 0 && clients.length === 0) {
              console.log("Another instance fetched data, updating local state");
              setClients(parsedData);
            }
          } catch (e) {
            console.error("Error parsing cached clients data:", e);
          }
        }
      }
    };
    
    // Listen for storage events
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('storage', handleFetchComplete);
    
    // Check for cached data on mount if we have no clients
    if (clients.length === 0) {
      const cachedData = localStorage.getItem("clients_cached_data");
      if (cachedData) {
        try {
          console.log("Loading clients from cache on mount");
          setClients(JSON.parse(cachedData));
        } catch (e) {
          console.error("Error parsing cached clients data:", e);
        }
      }
    }
    
    // Return cleanup function
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('storage', handleFetchComplete);
    };
  }, []);
  
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
