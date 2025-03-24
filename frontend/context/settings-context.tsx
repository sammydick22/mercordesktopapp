"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import * as settingsApi from "@/api/settings"

interface UserProfile {
  name?: string
  email: string
  timezone?: string
  hourly_rate?: number
  avatar_url?: string
}

interface AppSettings {
  screenshot_interval: number
  screenshot_quality: "low" | "medium" | "high"
  auto_sync_interval: number
  idle_detection_timeout: number
  theme: "light" | "dark" | "system"
  notifications_enabled: boolean
}

interface SettingsContextType {
  profile: UserProfile | null
  settings: AppSettings | null
  loading: boolean
  error: string | null
  fetchSettings: () => Promise<void>
  fetchProfile: () => Promise<void>
  updateSettings: (data: Partial<AppSettings>) => Promise<void>
  updateProfile: (data: Partial<UserProfile>) => Promise<void>
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>
  resetSettings: () => Promise<void>
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [settings, setSettings] = useState<AppSettings | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSettings = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await settingsApi.getSettings()
      // The API returns the settings directly, not wrapped in a "settings" object
      setSettings(data)
      console.log("Settings loaded:", data)
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to fetch settings")
      console.error("Error fetching settings:", err)
    } finally {
      setLoading(false)
    }
  }

  const fetchProfile = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await settingsApi.getUserProfile()
      // The API returns the profile directly, not wrapped in a "profile" object
      setProfile(data)
      console.log("Profile loaded:", data)
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to fetch profile")
      console.error("Error fetching profile:", err)
    } finally {
      setLoading(false)
    }
  }

  const updateSettings = async (settingsData: Partial<AppSettings>) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await settingsApi.updateSettings(settingsData)
      // The API returns the updated settings directly, not wrapped in a "settings" object
      setSettings(data)
      console.log("Settings updated:", data)
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to update settings")
      throw err
    } finally {
      setLoading(false)
    }
  }

  const updateProfile = async (profileData: Partial<UserProfile>) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await settingsApi.updateUserProfile(profileData)
      // The API returns the updated profile directly, not wrapped in a "profile" object
      setProfile(data)
      console.log("Profile updated:", data)
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to update profile")
      throw err
    } finally {
      setLoading(false)
    }
  }

  const changePassword = async (currentPassword: string, newPassword: string) => {
    setLoading(true)
    setError(null)
    try {
      await settingsApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to change password")
      throw err
    } finally {
      setLoading(false)
    }
  }

  const resetSettings = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await settingsApi.resetSettings()
      setSettings(data)
      console.log("Settings reset to defaults:", data)
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to reset settings")
      throw err
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Only fetch settings and profile when we have a user logged in
    const token = localStorage.getItem("auth_token")
    if (token) {
      console.log("[TIMER DEBUG] Settings context - Auth token found, fetching settings and profile")
      fetchSettings()
      fetchProfile()
    } else {
      console.log("[TIMER DEBUG] Settings context - No auth token found, skipping settings fetch")
    }
  }, [])

  // Add a second effect that runs when auth status might change
  useEffect(() => {
    const handleStorageChange = () => {
      const token = localStorage.getItem("auth_token")
      if (token && !profile) {
        console.log("Auth token changed, fetching settings and profile")
        fetchSettings()
        fetchProfile()
      }
    }

    // Listen for storage events (when token is added/removed)
    window.addEventListener('storage', handleStorageChange)
    
    // Check immediately as well
    handleStorageChange()
    
    return () => {
      window.removeEventListener('storage', handleStorageChange)
    }
  }, [profile])

  return (
    <SettingsContext.Provider
      value={{
        profile,
        settings,
        loading,
        error,
        fetchSettings,
        fetchProfile,
        updateSettings,
        updateProfile,
        changePassword,
        resetSettings,
      }}
    >
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  const context = useContext(SettingsContext)
  if (context === undefined) {
    throw new Error("useSettings must be used within a SettingsProvider")
  }
  return context
}
