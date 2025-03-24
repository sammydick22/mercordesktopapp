"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import * as organizationsApi from "@/api/organizations"
import * as settingsApi from "@/api/settings"

interface OrganizationMember {
  id: string
  user_id: string
  organization_id: string
  role: string
  name?: string
  email?: string
  avatar_url?: string
  joined_at: string
}

interface Organization {
  id: string
  name: string
  created_at: string
  updated_at: string
  settings?: Record<string, any>
  members?: OrganizationMember[]
  member_count?: number
}

interface OrganizationsContextType {
  organizations: Organization[]
  currentOrganization: Organization | null
  activeOrganizationId: string | null
  members: OrganizationMember[]
  loading: boolean
  error: string | null
  fetchOrganizations: () => Promise<void>
  fetchOrganization: (id: string) => Promise<Organization>
  createOrganization: (data: { name: string; settings?: Record<string, any> }) => Promise<Organization>
  updateOrganization: (id: string, data: { name?: string; settings?: Record<string, any> }) => Promise<Organization>
  deleteOrganization: (id: string) => Promise<void>
  fetchOrganizationMembers: (orgId: string) => Promise<OrganizationMember[]>
  addOrganizationMember: (orgId: string, data: { user_id: string; role: string }) => Promise<OrganizationMember>
  removeOrganizationMember: (orgId: string, userId: string) => Promise<void>
  createOrganizationInvitation: (orgId: string, data: { email: string; role?: string }) => Promise<any>
  setCurrentOrganization: (org: Organization | null) => void
  setActiveOrganization: (orgId: string) => Promise<void>
}

const OrganizationsContext = createContext<OrganizationsContextType | undefined>(undefined)

export function OrganizationsProvider({ children }: { children: ReactNode }) {
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null)
  const [activeOrganizationId, setActiveOrganizationId] = useState<string | null>(null)
  const [members, setMembers] = useState<OrganizationMember[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastFetchTime, setLastFetchTime] = useState<number>(0)
  const [fetchInProgress, setFetchInProgress] = useState<boolean>(false)

  // Enhanced fetch function with throttling, caching and retry logic
  const fetchOrganizations = async (retryCount = 0, force = false) => {
    // If no auth token yet, don't try to fetch
    const token = localStorage.getItem("auth_token");
    if (!token && !force) {
      console.log("No auth token available yet, will retry when available");
      return;
    }
    
    // GLOBAL THROTTLING: Use localStorage to share state between multiple component instances
    const now = Date.now();
    const globalLastFetchTime = parseInt(localStorage.getItem("orgs_global_last_fetch") || "0");
    const globalFetchInProgress = localStorage.getItem("orgs_fetch_in_progress") === "true";
    const timeSinceLastFetch = now - globalLastFetchTime;
    
    // Use cached data from localStorage if available
    const cachedData = localStorage.getItem("orgs_cached_data");
    if (cachedData && !force && organizations.length === 0) {
      try {
        const parsed = JSON.parse(cachedData);
        
        // Check if we actually need to update state to avoid re-render loops
        // Only set state if organizations is empty and parsed data isn't
        if (organizations.length === 0 && parsed.length > 0) {
          console.log("Using organizations data from localStorage cache");
          setOrganizations(parsed);
          
          // Set the first organization as current if none is selected
          if (parsed.length > 0 && !currentOrganization) {
            setCurrentOrganization(parsed[0]);
          }
        } else {
          console.log("Using cached data without state update");
        }
      } catch (e) {
        console.error("Error parsing cached organizations data:", e);
      }
    }
    
    // Return immediately if:
    // 1. A fetch is already in progress globally, OR
    // 2. It's been less than 30 seconds since the last fetch AND force is false AND we have data
    if (globalFetchInProgress) {
      console.log("Organizations fetch already in progress globally, skipping");
      return;
    }
    
    if (!force && timeSinceLastFetch < 30000 && (organizations.length > 0 || cachedData)) {
      console.log(`Using cached organizations data (last fetch: ${timeSinceLastFetch/1000}s ago)`);
      return;
    }
    
    // Set global in-progress flag
    localStorage.setItem("orgs_fetch_in_progress", "true");
    setFetchInProgress(true);
    setLoading(true);
    setError(null);
    
    try {
      console.log("Fetching organizations...");
      const { data } = await organizationsApi.getOrganizations();
      console.log("Organizations fetched:", data);
      
      // Update global last fetch time
      const fetchTime = Date.now();
      localStorage.setItem("orgs_global_last_fetch", fetchTime.toString());
      setLastFetchTime(fetchTime);
      
      // Handle response format
      if (data.organizations) {
        // Save to local state
        setOrganizations(data.organizations);
        
        // Cache data in localStorage
        try {
          localStorage.setItem("orgs_cached_data", JSON.stringify(data.organizations));
        } catch (e) {
          console.warn("Failed to cache organizations in localStorage:", e);
        }
        
        // Set the first organization as current if none is selected
        if (data.organizations.length > 0 && !currentOrganization) {
          setCurrentOrganization(data.organizations[0]);
        }
      } else {
        console.warn("Unexpected organizations response format:", data);
        setOrganizations([]);
      }
    } catch (err: any) {
      console.error("Error fetching organizations:", err);
      setError(err.response?.data?.message || "Failed to fetch organizations");
      
      // Enhanced retry logic with increasing delays
      if (retryCount < 3) {  // Reduced retry count
        // Calculate delay with exponential backoff (1s, 2s, 4s)
        const delay = Math.min(1000 * Math.pow(2, retryCount), 4000);
        console.log(`Retrying organizations fetch (${retryCount + 1}/3) in ${delay}ms...`);
        setTimeout(() => fetchOrganizations(retryCount + 1, force), delay);
        return;
      }
    } finally {
      setLoading(false);
      setFetchInProgress(false);
      localStorage.setItem("orgs_fetch_in_progress", "false");
    }
  }

  const fetchOrganization = async (id: string): Promise<Organization> => {
    try {
      const { data } = await organizationsApi.getOrganization(id)
      return data.organization
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to fetch organization")
    }
  }

  const createOrganization = async (orgData: {
    name: string
    settings?: Record<string, any>
  }): Promise<Organization> => {
    try {
      const { data } = await organizationsApi.createOrganization(orgData)
      setOrganizations((prev) => [...prev, data.organization])
      return data.organization
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to create organization")
    }
  }

  const updateOrganization = async (
    id: string,
    orgData: {
      name?: string
      settings?: Record<string, any>
    },
  ): Promise<Organization> => {
    try {
      const { data } = await organizationsApi.updateOrganization(id, orgData)
      setOrganizations((prev) => prev.map((org) => (org.id === id ? data.organization : org)))

      // Update current organization if it's the one being updated
      if (currentOrganization?.id === id) {
        setCurrentOrganization(data.organization)
      }

      return data.organization
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to update organization")
    }
  }

  const deleteOrganization = async (id: string): Promise<void> => {
    try {
      await organizationsApi.deleteOrganization(id)
      setOrganizations((prev) => prev.filter((org) => org.id !== id))

      // Clear current organization if it's the one being deleted
      if (currentOrganization?.id === id) {
        setCurrentOrganization(null)
      }
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to delete organization")
    }
  }

  const fetchOrganizationMembers = async (orgId: string): Promise<OrganizationMember[]> => {
    try {
      const { data } = await organizationsApi.getOrganizationMembers(orgId)
      setMembers(data.members || [])
      return data.members || []
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to fetch organization members")
    }
  }

  const addOrganizationMember = async (
    orgId: string,
    memberData: {
      user_id: string
      role: string
    },
  ): Promise<OrganizationMember> => {
    try {
      const { data } = await organizationsApi.addOrganizationMember(orgId, memberData)
      setMembers((prev) => [...prev, data.member])
      return data.member
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to add organization member")
    }
  }

  const removeOrganizationMember = async (orgId: string, userId: string): Promise<void> => {
    try {
      await organizationsApi.removeOrganizationMember(orgId, userId)
      setMembers((prev) => prev.filter((member) => member.user_id !== userId))
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to remove organization member")
    }
  }

  const createOrganizationInvitation = async (
    orgId: string,
    inviteData: {
      email: string
      role?: string
    },
  ): Promise<any> => {
    try {
      const { data } = await organizationsApi.createOrganizationInvitation(orgId, inviteData)
      return data.invitation
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to create organization invitation")
    }
  }

  // Set the active organization
  const setActiveOrganization = async (orgId: string): Promise<void> => {
    try {
      await settingsApi.setActiveOrganization(orgId)
      setActiveOrganizationId(orgId)
      
      // Also set as current organization for UI purposes
      const org = organizations.find(o => o.id === orgId)
      if (org) {
        setCurrentOrganization(org)
      }
    } catch (err: any) {
      console.error("Error setting active organization:", err)
      throw new Error(err.response?.data?.message || "Failed to set active organization")
    }
  }

  // Fetch user settings to get the active organization ID
  const fetchUserSettings = async () => {
    try {
      const { data } = await settingsApi.getSettings()
      if (data.active_organization_id) {
        setActiveOrganizationId(data.active_organization_id)
        
        // Also set as current organization for UI purposes
        const org = organizations.find(o => o.id === data.active_organization_id)
        if (org) {
          setCurrentOrganization(org)
        }
      }
    } catch (err) {
      console.error("Error fetching user settings:", err)
    }
  }

  // Clear in-progress flag on unmount to prevent deadlocks
  useEffect(() => {
    return () => {
      localStorage.setItem("orgs_fetch_in_progress", "false");
    };
  }, []);

  // Initial fetch effect - only runs once on mount
  useEffect(() => {
    fetchOrganizations();
    fetchUserSettings();
  }, []);
  
  // Add effect to fetch again when auth status changes
  useEffect(() => {
    // Listen for auth token changes
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === "auth_token" && event.newValue) {
        console.log("Auth token changed, fetching organizations");
        fetchOrganizations(0, true); // Force refresh with retryCount=0
      }
    };
    
    // Listen for global fetch completed events
    const handleFetchComplete = (event: StorageEvent) => {
      if (event.key === "orgs_global_last_fetch" && event.newValue) {
        // Another instance has completed a fetch, we should check our local state
        const cachedData = localStorage.getItem("orgs_cached_data");
        if (cachedData && organizations.length === 0) {
          try {
            const parsedData = JSON.parse(cachedData);
            // Only update state if there's actual data and our current state is empty
            if (parsedData && parsedData.length > 0 && organizations.length === 0) {
              console.log("Another instance fetched data, updating local state");
              setOrganizations(parsedData);
            }
          } catch (e) {
            console.error("Error parsing cached organizations data:", e);
          }
        }
      }
    };
    
    // Listen for storage events
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('storage', handleFetchComplete);
    
    // Check for cached data on mount if we have no organizations
    if (organizations.length === 0) {
      const cachedData = localStorage.getItem("orgs_cached_data");
      if (cachedData) {
        try {
          console.log("Loading organizations from cache on mount");
          setOrganizations(JSON.parse(cachedData));
        } catch (e) {
          console.error("Error parsing cached organizations data:", e);
        }
      }
    }
    
    // Return cleanup function
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('storage', handleFetchComplete);
    };
  }, []);

  useEffect(() => {
    if (currentOrganization) {
      fetchOrganizationMembers(currentOrganization.id)
    }
  }, [currentOrganization])

  return (
    <OrganizationsContext.Provider
      value={{
        organizations,
        currentOrganization,
        activeOrganizationId,
        members,
        loading,
        error,
        fetchOrganizations,
        fetchOrganization,
        createOrganization,
        updateOrganization,
        deleteOrganization,
        fetchOrganizationMembers,
        addOrganizationMember,
        removeOrganizationMember,
        createOrganizationInvitation,
        setCurrentOrganization,
        setActiveOrganization,
      }}
    >
      {children}
    </OrganizationsContext.Provider>
  )
}

export function useOrganizations() {
  const context = useContext(OrganizationsContext)
  if (context === undefined) {
    throw new Error("useOrganizations must be used within an OrganizationsProvider")
  }
  return context
}
