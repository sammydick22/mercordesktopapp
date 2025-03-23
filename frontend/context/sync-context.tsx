"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import * as syncApi from "@/api/sync"

interface SyncStatus {
  initialized: boolean
  is_syncing: boolean
  sync_error?: string
  last_sync: {
    activity_logs?: {
      last_id: number
      last_time: string
    }
    screenshots?: {
      last_id: number
      last_time: string
    }
  }
}

interface SyncContextType {
  syncStatus: SyncStatus | null
  loading: boolean
  syncAll: () => Promise<void>
  syncActivities: () => Promise<void>
  syncScreenshots: () => Promise<void>
  syncOrganization: () => Promise<void>
  startBackgroundSync: () => Promise<void>
}

const SyncContext = createContext<SyncContextType | undefined>(undefined)

export function SyncProvider({ children }: { children: ReactNode }) {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchSyncStatus = async () => {
    try {
      const { data } = await syncApi.getSyncStatus()
      setSyncStatus(data)
    } catch (err) {
      console.error("Error fetching sync status:", err)
    }
  }

  useEffect(() => {
    fetchSyncStatus()

    // Poll for sync status updates every minute
    const interval = setInterval(() => {
      fetchSyncStatus()
    }, 60000)

    return () => clearInterval(interval)
  }, [])

  const syncAll = async () => {
    setLoading(true)
    try {
      await syncApi.syncAll()
      await fetchSyncStatus()
    } catch (err) {
      console.error("Error syncing all data:", err)
    } finally {
      setLoading(false)
    }
  }

  const syncActivities = async () => {
    setLoading(true)
    try {
      await syncApi.syncActivities()
      await fetchSyncStatus()
    } catch (err) {
      console.error("Error syncing activities:", err)
    } finally {
      setLoading(false)
    }
  }

  const syncScreenshots = async () => {
    setLoading(true)
    try {
      await syncApi.syncScreenshots()
      await fetchSyncStatus()
    } catch (err) {
      console.error("Error syncing screenshots:", err)
    } finally {
      setLoading(false)
    }
  }

  const syncOrganization = async () => {
    setLoading(true)
    try {
      await syncApi.syncOrganization()
      await fetchSyncStatus()
    } catch (err) {
      console.error("Error syncing organization data:", err)
    } finally {
      setLoading(false)
    }
  }

  const startBackgroundSync = async () => {
    try {
      await syncApi.startBackgroundSync()
      await fetchSyncStatus()
    } catch (err) {
      console.error("Error starting background sync:", err)
    }
  }

  return (
    <SyncContext.Provider
      value={{
        syncStatus,
        loading,
        syncAll,
        syncActivities,
        syncScreenshots,
        syncOrganization,
        startBackgroundSync,
      }}
    >
      {children}
    </SyncContext.Provider>
  )
}

export function useSync() {
  const context = useContext(SyncContext)
  if (context === undefined) {
    throw new Error("useSync must be used within a SyncProvider")
  }
  return context
}

