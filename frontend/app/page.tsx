"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/auth-context"
import { useTimeTracking } from "@/context/time-tracking-context"
import { useSync } from "@/context/sync-context"
import * as screenshotsApi from "@/api/screenshots"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { formatDateTime, formatDuration, formatTime } from "@/lib/utils"
import { Clock, BarChart, ImageIcon, RefreshCw, ArrowUpRight, Zap, Activity } from "lucide-react"
import TimeEntryList from "@/components/time-entry-list"
import ScreenshotGallery from "@/components/screenshot-gallery"
import { motion } from "framer-motion"

export default function Dashboard() {
  const { user, loading: authLoading } = useAuth()
  const { currentTimeEntry, recentEntries, loadRecentEntries } = useTimeTracking()
  const { syncStatus, syncAll } = useSync()
  const router = useRouter()
  const [screenshots, setScreenshots] = useState<any[]>([])
  const [loadingScreenshots, setLoadingScreenshots] = useState(true)

  // Function to determine if a timestamp is from today
  const isToday = (timestamp: string) => {
    const date = new Date(timestamp);
    const today = new Date();
    return date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear();
  };

  // Get screenshots data
  useEffect(() => {
    const fetchScreenshots = async () => {
      try {
        setLoadingScreenshots(true);
        const { data } = await screenshotsApi.getScreenshots(100, 0);
        setScreenshots(data.screenshots || []);
      } catch (err) {
        console.error("Error fetching screenshots:", err);
      } finally {
        setLoadingScreenshots(false);
      }
    };

    if (user) {
      fetchScreenshots();
    }
  }, [user]);

  // Handle capturing a new screenshot
  const handleCaptureScreenshot = async () => {
    try {
      await screenshotsApi.captureScreenshot();
      // Refresh screenshots
      const { data } = await screenshotsApi.getScreenshots(100, 0);
      setScreenshots(data.screenshots || []);
    } catch (err) {
      console.error("Error capturing screenshot:", err);
    }
  };

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login")
    }
  }, [user, authLoading, router])

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

  const totalDuration = recentEntries.reduce((total, entry) => {
    return total + (entry.duration || 0)
  }, 0)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <motion.h1
          className="text-3xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          Dashboard
        </motion.h1>
        <Button
          onClick={() => syncAll()}
          disabled={syncStatus?.is_syncing}
          className="bg-[#1E293B] hover:bg-[#2D3748] text-white font-medium rounded-full px-6 py-2.5 flex items-center gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${syncStatus?.is_syncing ? "animate-spin" : ""}`} />
          Sync Data
        </Button>
      </div>

      <motion.div
        className="grid gap-6 md:grid-cols-2 lg:grid-cols-4"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 p-6">
            <CardTitle className="text-sm font-medium text-gray-300">Current Status</CardTitle>
            <div className="rounded-full bg-[#1E293B] p-2">
              <Clock className="h-4 w-4 text-blue-500" />
            </div>
          </CardHeader>
          <CardContent className="p-6 pt-0">
            <div className="flex flex-col gap-1">
              <div className="text-2xl font-bold">
                {currentTimeEntry?.is_active ? (
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600">
                    Active
                  </span>
                ) : (
                  "Inactive"
                )}
              </div>
              <p className="text-xs text-gray-400">
                {currentTimeEntry?.is_active
                  ? `Started at ${formatTime(currentTimeEntry.start_time)}`
                  : "No active time entry"}
              </p>
              {currentTimeEntry?.is_active && (
                <div className="mt-2">
                  <div className="bg-blue-500/10 text-blue-500 rounded-full px-2.5 py-0.5 text-xs font-medium inline-flex">
                    {currentTimeEntry.description || "No description"}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 p-6">
            <CardTitle className="text-sm font-medium text-gray-300">Today's Hours</CardTitle>
            <div className="rounded-full bg-[#1E293B] p-2">
              <BarChart className="h-4 w-4 text-blue-500" />
            </div>
          </CardHeader>
          <CardContent className="p-6 pt-0">
            <div className="flex flex-col gap-1">
              <div className="text-2xl font-bold">{formatDuration(totalDuration)}</div>
              <p className="text-xs text-gray-400">Across {recentEntries.length} time entries</p>
              <div className="mt-2 w-full bg-[#1E293B] rounded-full h-1.5">
                <div
                  className="bg-gradient-to-r from-blue-500 to-purple-600 h-1.5 rounded-full"
                  style={{ width: `${Math.min(100, (totalDuration / (8 * 3600)) * 100)}%` }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 p-6">
            <CardTitle className="text-sm font-medium text-gray-300">Screenshots</CardTitle>
            <div className="rounded-full bg-[#1E293B] p-2">
              <ImageIcon className="h-4 w-4 text-blue-500" />
            </div>
          </CardHeader>
          <CardContent className="p-6 pt-0">
            <div className="flex flex-col gap-1">
              {loadingScreenshots ? (
                <div className="text-2xl font-bold flex items-center">
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin text-blue-500" />
                  Loading...
                </div>
              ) : (
                <div className="text-2xl font-bold">
                  {screenshots.filter(ss => isToday(ss.timestamp)).length}
                </div>
              )}
              <p className="text-xs text-gray-400">Captured today</p>
              <div className="mt-2">
                <Button 
                  variant="link" 
                  className="p-0 h-auto text-xs text-blue-500 flex items-center gap-1"
                  onClick={handleCaptureScreenshot}
                >
                  Capture now
                  <ArrowUpRight size={12} />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 p-6">
            <CardTitle className="text-sm font-medium text-gray-300">Sync Status</CardTitle>
            <div className="rounded-full bg-[#1E293B] p-2">
              <Activity className="h-4 w-4 text-blue-500" />
            </div>
          </CardHeader>
          <CardContent className="p-6 pt-0">
            <div className="flex flex-col gap-1">
              <div className="text-2xl font-bold">
                {syncStatus?.is_syncing ? (
                  <span className="flex items-center gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Syncing
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-green-500" />
                    Ready
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-400">
                {syncStatus?.last_sync?.activity_logs
                  ? `Last sync: ${formatDateTime(syncStatus.last_sync.activity_logs.last_time)}`
                  : "Not synced yet"}
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
      >
        <Tabs defaultValue="recent" className="relative">
          <TabsList className="inline-flex h-10 items-center justify-center rounded-lg bg-[#1E293B] p-1 text-gray-400">
            <TabsTrigger
              value="recent"
              className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-[#0F172A] data-[state=active]:text-white data-[state=active]:shadow-sm"
            >
              Recent Activity
            </TabsTrigger>
            <TabsTrigger
              value="screenshots"
              className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-[#0F172A] data-[state=active]:text-white data-[state=active]:shadow-sm"
            >
              Recent Screenshots
            </TabsTrigger>
          </TabsList>
          <TabsContent value="recent" className="space-y-4 mt-2">
            <TimeEntryList entries={recentEntries} />
          </TabsContent>
          <TabsContent value="screenshots" className="mt-2">
            <ScreenshotGallery />
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  )
}
