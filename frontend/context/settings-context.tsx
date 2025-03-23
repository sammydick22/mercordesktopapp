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
      setSettings(data.settings)
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
      setProfile(data.profile)
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
      setSettings(data.settings)
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
      setProfile(data.profile)
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

  useEffect(() => {
    fetchSettings()
    fetchProfile()
  }, [])

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

