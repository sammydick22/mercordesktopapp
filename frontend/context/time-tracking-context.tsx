"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import * as timeEntriesApi from "@/api/timeEntries"
import { useSettings } from "@/context/settings-context"
import { calculateElapsedTime } from "@/lib/timezone-utils"

interface TimeEntry {
  id: string
  start_time: string
  end_time?: string
  duration?: number
  project_id?: string
  task_id?: string
  description?: string
  is_active: boolean
  synced: boolean
}

interface TimeTrackingContextType {
  currentTimeEntry: TimeEntry | null
  recentEntries: TimeEntry[]
  loading: boolean
  error: string | null
  startTimeEntry: (projectId?: string, taskId?: string, description?: string) => Promise<void>
  stopTimeEntry: (description?: string) => Promise<void>
  refreshCurrentEntry: () => Promise<void>
  loadRecentEntries: (limit?: number) => Promise<void>
  localStartTime: string | null
}

const TimeTrackingContext = createContext<TimeTrackingContextType | undefined>(undefined)

export function TimeTrackingProvider({ children }: { children: ReactNode }) {
  const { profile } = useSettings()
  const [currentTimeEntry, setCurrentTimeEntry] = useState<TimeEntry | null>(null)
  const [recentEntries, setRecentEntries] = useState<TimeEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [localStartTime, setLocalStartTime] = useState<string | null>(null)

  const refreshCurrentEntry = async () => {
    try {
      console.log("[TIMER DEBUG] Fetching current time entry");
      const { data } = await timeEntriesApi.getCurrentTimeEntry();
      console.log("[TIMER DEBUG] Received current time entry:", data.time_entry);
      
      // If we got an active time entry from the server
      if (data.time_entry && data.time_entry.is_active) {
        // Store the local start time for continuity if we have one
        // and only if this is our first time getting the server entry
        if (localStartTime && (!currentTimeEntry || !currentTimeEntry.is_active)) {
          console.log("[TIMER DEBUG] Preserving local start time for continuity:", localStartTime);
          // Instead of clearing localStartTime, we keep it
          // This ensures the elapsed time calculation remains consistent
        } else {
          // If this is a subsequent polling update, we can clear localStartTime
          // as we'll be using the server timestamp fully now
          console.log("[TIMER DEBUG] Already have server entry, can clear localStartTime");
          setLocalStartTime(null);
        }
      } else if (!data.time_entry || !data.time_entry.is_active) {
        // No active time entry, clear local start time
        console.log("[TIMER DEBUG] No active time entry, clearing localStartTime");
        setLocalStartTime(null);
      }
      
      setCurrentTimeEntry(data.time_entry || null);
    } catch (err) {
      console.error("[TIMER DEBUG] Error fetching current time entry:", err);
    }
  }

  const loadRecentEntries = async (limit = 5) => {
    setLoading(true)
    try {
      const { data } = await timeEntriesApi.getTimeEntries(limit, 0)
      setRecentEntries(data.time_entries || [])
    } catch (err) {
      console.error("Error fetching recent time entries:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refreshCurrentEntry()
    loadRecentEntries()

    // Poll for updates every 30 seconds
    const interval = setInterval(() => {
      refreshCurrentEntry()
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const startTimeEntry = async (projectId?: string, taskId?: string, description?: string) => {
    setLoading(true)
    setError(null)
    
    // Save the local start time immediately for optimistic updates
    const now = new Date().toISOString();
    setLocalStartTime(now);
    
    try {
      const { data } = await timeEntriesApi.startTimeEntry(projectId, taskId, description)
      setCurrentTimeEntry(data.time_entry)
      await loadRecentEntries()
    } catch (err: any) {
      // Clear the local start time if there's an error
      setLocalStartTime(null);
      setError(err.response?.data?.message || "Failed to start time entry")
      throw err
    } finally {
      setLoading(false)
    }
  }

  const stopTimeEntry = async (description?: string) => {
    if (!currentTimeEntry) return

    setLoading(true)
    setError(null)
    try {
      const { data } = await timeEntriesApi.stopTimeEntry(description)
      setCurrentTimeEntry(data.time_entry)
      await loadRecentEntries()
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to stop time entry")
      throw err
    } finally {
      setLoading(false)
    }
  }

  return (
    <TimeTrackingContext.Provider
      value={{
        currentTimeEntry,
        recentEntries,
        loading,
        error,
        startTimeEntry,
        stopTimeEntry,
        refreshCurrentEntry,
        loadRecentEntries,
        localStartTime
      }}
    >
      {children}
    </TimeTrackingContext.Provider>
  )
}

export function useTimeTracking() {
  const context = useContext(TimeTrackingContext)
  if (context === undefined) {
    throw new Error("useTimeTracking must be used within a TimeTrackingProvider")
  }
  return context
}
