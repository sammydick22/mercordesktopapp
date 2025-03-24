"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/auth-context"
import { useSettings } from "@/context/settings-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, RefreshCw, User, Settings, Bell, Save, Moon, Sun, Laptop } from "lucide-react"
import { motion } from "framer-motion"

export default function SettingsPage() {
  const { user, loading: authLoading } = useAuth()
  const { profile, settings, loading, error, updateSettings, updateProfile, changePassword, resetSettings } = useSettings()
  const [activeTab, setActiveTab] = useState("profile")
  const [formProfile, setFormProfile] = useState({
    name: "",
    email: "",
    timezone: "",
    hourly_rate: 0,
  })
  const [formPassword, setFormPassword] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  })
  const [formSettings, setFormSettings] = useState({
    screenshot_interval: 5,
    screenshot_quality: "medium" as "low" | "medium" | "high",
    auto_sync_interval: 5,
    idle_detection_timeout: 5,
    theme: "dark" as "light" | "dark" | "system",
    notifications_enabled: true,
  })
  const [passwordError, setPasswordError] = useState("")
  const [successMessage, setSuccessMessage] = useState("")
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login")
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (profile) {
      setFormProfile({
        name: profile.name || "",
        email: profile.email,
        timezone: profile.timezone || "",
        hourly_rate: profile.hourly_rate || 0,
      })
    }
  }, [profile])

  useEffect(() => {
    if (settings) {
      setFormSettings({
        screenshot_interval: settings.screenshot_interval,
        screenshot_quality: settings.screenshot_quality,
        auto_sync_interval: settings.auto_sync_interval,
        idle_detection_timeout: settings.idle_detection_timeout,
        theme: settings.theme,
        notifications_enabled: settings.notifications_enabled,
      })
    }
  }, [settings])

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSuccessMessage("")
    try {
      await updateProfile(formProfile)
      setSuccessMessage("Profile updated successfully")
      setTimeout(() => setSuccessMessage(""), 3000)
    } catch (err) {
      console.error("Error updating profile:", err)
    }
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError("")
    setSuccessMessage("")

    if (formPassword.new_password !== formPassword.confirm_password) {
      setPasswordError("New passwords do not match")
      return
    }

    try {
      await changePassword(formPassword.current_password, formPassword.new_password)
      setSuccessMessage("Password changed successfully")
      setFormPassword({
        current_password: "",
        new_password: "",
        confirm_password: "",
      })
      setTimeout(() => setSuccessMessage(""), 3000)
    } catch (err) {
      console.error("Error changing password:", err)
      setPasswordError("Failed to change password. Please check your current password.")
    }
  }

  const handleSettingsSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSuccessMessage("")
    try {
      await updateSettings(formSettings)
      setSuccessMessage("Settings updated successfully")
      setTimeout(() => setSuccessMessage(""), 3000)
    } catch (err) {
      console.error("Error updating settings:", err)
    }
  }

  const applyTheme = (theme: "light" | "dark" | "system") => {
    const html = document.querySelector("html")
    if (theme === "dark") {
      html?.classList.add("dark")
    } else if (theme === "light") {
      html?.classList.remove("dark")
    } else {
      // System preference
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
      if (prefersDark) {
        html?.classList.add("dark")
      } else {
        html?.classList.remove("dark")
      }
    }
    setFormSettings({ ...formSettings, theme })
  }

  if (authLoading || !user) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-4">
          <div className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600 text-2xl font-bold">
            TimeTracker
          </div>
          <div className="animate-spin">
            <RefreshCw size={24} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <motion.h1
        className="text-3xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        Settings
      </motion.h1>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="relative">
        <TabsList className="inline-flex h-10 items-center justify-center rounded-lg bg-[#1E293B] p-1 text-gray-400">
          <TabsTrigger
            value="profile"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-[#0F172A] data-[state=active]:text-white data-[state=active]:shadow-sm"
          >
            <User className="mr-2 h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger
            value="app"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-[#0F172A] data-[state=active]:text-white data-[state=active]:shadow-sm"
          >
            <Settings className="mr-2 h-4 w-4" />
            App Settings
          </TabsTrigger>
          <TabsTrigger
            value="notifications"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-[#0F172A] data-[state=active]:text-white data-[state=active]:shadow-sm"
          >
            <Bell className="mr-2 h-4 w-4" />
            Notifications
          </TabsTrigger>
        </TabsList>

        {successMessage && (
          <Alert className="mt-4 bg-green-500/10 border-green-500/20 text-green-500">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{successMessage}</AlertDescription>
          </Alert>
        )}

        <TabsContent value="profile" className="mt-4 space-y-6">
          <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
            <CardHeader>
              <CardTitle className="text-xl font-semibold text-white">User Profile</CardTitle>
              <CardDescription className="text-gray-400">Manage your personal information</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleProfileSubmit} className="space-y-6">
                <div className="flex items-center gap-6">
                  <Avatar className="h-20 w-20 border-2 border-[#1E293B]">
                    <AvatarImage src={`https://avatar.vercel.sh/${user.email}`} />
                    <AvatarFallback className="bg-[#1E293B] text-lg">
                      {user.email.substring(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h3 className="text-lg font-medium text-white">{formProfile.name || user.email}</h3>
                    <p className="text-sm text-gray-400">{user.email}</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    <Input
                      id="name"
                      placeholder="Your full name"
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                      value={formProfile.name}
                      onChange={(e) => setFormProfile({ ...formProfile, name: e.target.value })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="Your email address"
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                      value={formProfile.email}
                      onChange={(e) => setFormProfile({ ...formProfile, email: e.target.value })}
                      disabled
                    />
                    <p className="text-xs text-gray-500">Email cannot be changed</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="timezone">Timezone</Label>
                    <select
                      id="timezone"
                      className="flex h-10 w-full rounded-md border px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm bg-[#1E293B] border-[#2D3748] text-white"
                      value={formProfile.timezone}
                      onChange={(e) => setFormProfile({ ...formProfile, timezone: e.target.value })}
                    >
                      <option value="" className="text-gray-400">Select timezone</option>
                      <option value="UTC" className="text-white">UTC</option>
                      <option value="America/New_York" className="text-white">Eastern Time (ET)</option>
                      <option value="America/Chicago" className="text-white">Central Time (CT)</option>
                      <option value="America/Denver" className="text-white">Mountain Time (MT)</option>
                      <option value="America/Los_Angeles" className="text-white">Pacific Time (PT)</option>
                      <option value="Europe/London" className="text-white">London (GMT)</option>
                      <option value="Europe/Paris" className="text-white">Paris (CET)</option>
                      <option value="Asia/Tokyo" className="text-white">Tokyo (JST)</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="hourly_rate">Default Hourly Rate ($)</Label>
                    <Input
                      id="hourly_rate"
                      type="number"
                      placeholder="Your default hourly rate"
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                      value={formProfile.hourly_rate}
                      onChange={(e) =>
                        setFormProfile({ ...formProfile, hourly_rate: Number.parseFloat(e.target.value) })
                      }
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5"
                >
                  <Save className="mr-2 h-4 w-4" />
                  Save Profile
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
            <CardHeader>
              <CardTitle className="text-xl font-semibold text-white">Change Password</CardTitle>
              <CardDescription className="text-gray-400">Update your account password</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handlePasswordSubmit} className="space-y-6">
                {passwordError && (
                  <Alert className="bg-red-500/10 border-red-500/20 text-red-500">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{passwordError}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="current_password">Current Password</Label>
                    <Input
                      id="current_password"
                      type="password"
                      placeholder="Your current password"
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                      value={formPassword.current_password}
                      onChange={(e) => setFormPassword({ ...formPassword, current_password: e.target.value })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="new_password">New Password</Label>
                    <Input
                      id="new_password"
                      type="password"
                      placeholder="Your new password"
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                      value={formPassword.new_password}
                      onChange={(e) => setFormPassword({ ...formPassword, new_password: e.target.value })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirm_password">Confirm New Password</Label>
                    <Input
                      id="confirm_password"
                      type="password"
                      placeholder="Confirm your new password"
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                      value={formPassword.confirm_password}
                      onChange={(e) => setFormPassword({ ...formPassword, confirm_password: e.target.value })}
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5"
                  disabled={
                    !formPassword.current_password || !formPassword.new_password || !formPassword.confirm_password
                  }
                >
                  <Save className="mr-2 h-4 w-4" />
                  Change Password
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="app" className="mt-4 space-y-6">
          <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
            <CardHeader>
              <CardTitle className="text-xl font-semibold text-white">Application Settings</CardTitle>
              <CardDescription className="text-gray-400">Configure how the application works</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSettingsSubmit} className="space-y-6">
                <div className="space-y-6">
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-white">Theme</h3>
                    <div className="flex items-center gap-4">
                      <Button
                        type="button"
                        variant="outline"
                        className={`flex-1 bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B] ${formSettings.theme === "light" ? "bg-[#1E293B] border-blue-500" : ""}`}
                        onClick={() => applyTheme("light")}
                      >
                        <Sun className="mr-2 h-4 w-4" />
                        Light
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        className={`flex-1 bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B] ${formSettings.theme === "dark" ? "bg-[#1E293B] border-blue-500" : ""}`}
                        onClick={() => applyTheme("dark")}
                      >
                        <Moon className="mr-2 h-4 w-4" />
                        Dark
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        className={`flex-1 bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B] ${formSettings.theme === "system" ? "bg-[#1E293B] border-blue-500" : ""}`}
                        onClick={() => applyTheme("system")}
                      >
                        <Laptop className="mr-2 h-4 w-4" />
                        System
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-white">Time Tracking</h3>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="idle_detection">Idle Detection Timeout (minutes)</Label>
                        <span className="text-sm text-gray-400">{formSettings.idle_detection_timeout} min</span>
                      </div>
                      <Slider
                        id="idle_detection"
                        min={1}
                        max={30}
                        step={1}
                        value={[formSettings.idle_detection_timeout]}
                        onValueChange={(value) =>
                          setFormSettings({ ...formSettings, idle_detection_timeout: value[0] })
                        }
                        className="w-full"
                      />
                      <p className="text-xs text-gray-500">
                        Detect when you're idle and prompt to continue or discard time
                      </p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-white">Screenshots</h3>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="screenshot_interval">Screenshot Interval (minutes)</Label>
                        <span className="text-sm text-gray-400">{formSettings.screenshot_interval} min</span>
                      </div>
                      <Slider
                        id="screenshot_interval"
                        min={1}
                        max={30}
                        step={1}
                        value={[formSettings.screenshot_interval]}
                        onValueChange={(value) => setFormSettings({ ...formSettings, screenshot_interval: value[0] })}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-500">
                        How often screenshots are taken during active time tracking
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="screenshot_quality">Screenshot Quality</Label>
                      <select
                        id="screenshot_quality"
                        className="flex h-10 w-full rounded-md border px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm bg-[#1E293B] border-[#2D3748] text-white"
                        value={formSettings.screenshot_quality}
                        onChange={(e) => setFormSettings({ ...formSettings, screenshot_quality: e.target.value as "low" | "medium" | "high" })}
                      >
                        <option value="low" className="text-white">Low (smaller file size)</option>
                        <option value="medium" className="text-white">Medium (balanced)</option>
                        <option value="high" className="text-white">High (better quality)</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-white">Synchronization</h3>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="auto_sync_interval">Auto-Sync Interval (minutes)</Label>
                        <span className="text-sm text-gray-400">{formSettings.auto_sync_interval} min</span>
                      </div>
                      <Slider
                        id="auto_sync_interval"
                        min={1}
                        max={60}
                        step={1}
                        value={[formSettings.auto_sync_interval]}
                        onValueChange={(value) => setFormSettings({ ...formSettings, auto_sync_interval: value[0] })}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-500">
                        How often data is automatically synchronized with the server
                      </p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-white">Database Maintenance</h3>
                    
                    <div className="space-y-2">
                      <div className="flex flex-col space-y-2">
                        <div className="flex justify-between items-center">
                          <div>
                            <Label>Clean up orphaned organization memberships</Label>
                            <p className="text-xs text-gray-500">
                              Remove memberships that reference non-existent organizations
                            </p>
                          </div>
                          <Button
                            type="button"
                            variant="outline"
                            className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
                            onClick={async () => {
                              try {
                                const { cleanupOrphanedMemberships } = await import('@/api/organizations');
                                const result = await cleanupOrphanedMemberships();
                                setSuccessMessage(`Successfully cleaned up ${result.data.orphaned_count} orphaned memberships`);
                                setTimeout(() => setSuccessMessage(""), 5000);
                              } catch (error) {
                                console.error("Error cleaning up orphaned memberships:", error);
                              }
                            }}
                          >
                            Clean Up
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-between">
                  <Button
                    type="button"
                    variant="outline"
                    className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
                    onClick={() => {
                      resetSettings()
                        .then(() => setSuccessMessage("Settings reset to defaults successfully"))
                        .catch((err) => console.error("Error resetting settings:", err));
                    }}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Reset to Defaults
                  </Button>
                  <Button
                    type="submit"
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5"
                  >
                    <Save className="mr-2 h-4 w-4" />
                    Save Settings
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="mt-4 space-y-6">
          <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
            <CardHeader>
              <CardTitle className="text-xl font-semibold text-white">Notification Settings</CardTitle>
              <CardDescription className="text-gray-400">
                Configure how and when you receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSettingsSubmit} className="space-y-6">
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="notifications_enabled">Enable Notifications</Label>
                      <p className="text-sm text-gray-400">Receive desktop notifications</p>
                    </div>
                    <Switch
                      id="notifications_enabled"
                      checked={formSettings.notifications_enabled}
                      onCheckedChange={(checked) =>
                        setFormSettings({ ...formSettings, notifications_enabled: checked })
                      }
                    />
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-white">Notification Types</h3>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Idle Detection</Label>
                          <p className="text-sm text-gray-400">When you've been idle for the set time</p>
                        </div>
                        <Switch checked={true} disabled={!formSettings.notifications_enabled} />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Sync Completed</Label>
                          <p className="text-sm text-gray-400">When data synchronization completes</p>
                        </div>
                        <Switch checked={true} disabled={!formSettings.notifications_enabled} />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Sync Errors</Label>
                          <p className="text-sm text-gray-400">When there's an error during synchronization</p>
                        </div>
                        <Switch checked={true} disabled={!formSettings.notifications_enabled} />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Screenshot Taken</Label>
                          <p className="text-sm text-gray-400">When a screenshot is captured</p>
                        </div>
                        <Switch checked={true} disabled={!formSettings.notifications_enabled} />
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Timer Reminders</Label>
                          <p className="text-sm text-gray-400">Periodic reminders when tracking time</p>
                        </div>
                        <Switch checked={false} disabled={!formSettings.notifications_enabled} />
                      </div>
                    </div>
                  </div>
                </div>

                <Button
                  type="submit"
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5"
                >
                  <Save className="mr-2 h-4 w-4" />
                  Save Notification Settings
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
