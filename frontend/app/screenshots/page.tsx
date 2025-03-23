"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"
import { useAuth } from "@/context/auth-context"
import { useProjects } from "@/context/projects-context"
import * as screenshotsApi from "@/api/screenshots"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { DatePicker } from "@/components/ui/date-picker"
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog"
import { Camera, Filter, Download, Share2, Trash2, X, Clock, RefreshCw } from "lucide-react"
import { motion } from "framer-motion"
import { formatDateTime } from "@/lib/utils"

interface Screenshot {
  id: string
  timestamp: string
  filepath: string
  thumbnail_path: string
  time_entry_id?: string
  synced: boolean
}

export default function ScreenshotsPage() {
  const { user, loading: authLoading } = useAuth()
  const { activeProjects } = useProjects()
  const [screenshots, setScreenshots] = useState<Screenshot[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [filterStartDate, setFilterStartDate] = useState<Date | undefined>(undefined)
  const [filterEndDate, setFilterEndDate] = useState<Date | undefined>(undefined)
  const [filterProject, setFilterProject] = useState<string | undefined>(undefined)
  const [showFilters, setShowFilters] = useState(false)
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login")
    }
  }, [user, authLoading, router])

  useEffect(() => {
    fetchScreenshots()
  }, [])

  const fetchScreenshots = async () => {
    setLoading(true)
    try {
      const { data } = await screenshotsApi.getScreenshots(100, 0)
      setScreenshots(data.screenshots || [])
    } catch (err) {
      console.error("Error fetching screenshots:", err)
    } finally {
      setLoading(false)
    }
  }

  const captureScreenshot = async () => {
    try {
      await screenshotsApi.captureScreenshot()
      fetchScreenshots()
    } catch (err) {
      console.error("Error capturing screenshot:", err)
    }
  }

  const filteredScreenshots = screenshots.filter((screenshot) => {
    // Date filters
    const screenshotDate = new Date(screenshot.timestamp)
    const matchesStartDate = !filterStartDate || screenshotDate >= filterStartDate
    const matchesEndDate = !filterEndDate || screenshotDate <= filterEndDate

    // We don't have project info in the screenshot data, so we'd need to join with time entries
    // For now, we'll just filter by date

    return matchesStartDate && matchesEndDate
  })

  const clearFilters = () => {
    setFilterStartDate(undefined)
    setFilterEndDate(undefined)
    setFilterProject(undefined)
    setSearchQuery("")
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
      <motion.div
        className="flex items-center justify-between"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="text-3xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600">
          Screenshots
        </h1>
        <div className="flex items-center gap-4">
          <Dialog open={showFilters} onOpenChange={setShowFilters}>
            <DialogTrigger asChild>
              <Button variant="outline" className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]">
                <Filter className="mr-2 h-4 w-4" />
                Filter
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-[#0F172A] border-[#1E293B] text-white">
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="start_date">Start Date</Label>
                    <DatePicker
                      date={filterStartDate}
                      setDate={setFilterStartDate}
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="end_date">End Date</Label>
                    <DatePicker
                      date={filterEndDate}
                      setDate={setFilterEndDate}
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                    />
                  </div>
                </div>

                <div className="flex justify-between mt-4">
                  <Button
                    variant="outline"
                    onClick={clearFilters}
                    className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
                  >
                    Clear Filters
                  </Button>
                  <Button
                    onClick={() => setShowFilters(false)}
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                  >
                    Apply Filters
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          <Button
            onClick={captureScreenshot}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5"
          >
            <Camera className="mr-2 h-4 w-4" />
            Capture Screenshot
          </Button>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 p-6">
            <div>
              <CardTitle className="text-xl font-semibold text-white">Screenshot Gallery</CardTitle>
              <CardDescription className="text-gray-400">
                {filteredScreenshots.length} screenshots found
                {(filterStartDate || filterEndDate) && " (filtered)"}
              </CardDescription>
            </div>
            {(filterStartDate || filterEndDate) && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearFilters}
                className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
              >
                Clear Filters
              </Button>
            )}
          </CardHeader>
          <CardContent className="p-6">
            {loading ? (
              <div className="flex justify-center py-8">
                <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
              </div>
            ) : filteredScreenshots.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <div className="flex flex-col items-center gap-3">
                  <Camera className="h-12 w-12 text-gray-500/50" />
                  <p>No screenshots found</p>
                  <Button
                    onClick={captureScreenshot}
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5 mt-2"
                  >
                    <Camera className="mr-2 h-4 w-4" />
                    Capture Screenshot
                  </Button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {filteredScreenshots.map((screenshot, index) => (
                  <motion.div
                    key={screenshot.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <Dialog>
                      <DialogTrigger asChild>
                        <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden transition-all duration-300 hover:transform hover:-translate-y-1 cursor-pointer">
                          <CardContent className="p-2">
                            <div className="aspect-video relative overflow-hidden rounded-md">
                              <Image
                                src={screenshotsApi.getScreenshotThumbnailUrl(screenshot.id) || "/placeholder.svg"}
                                alt={`Screenshot from ${formatDateTime(screenshot.timestamp)}`}
                                fill
                                className="object-cover"
                              />
                              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-200">
                                <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between">
                                  <div className="text-xs text-white flex items-center">
                                    <Clock className="mr-1 h-3 w-3" />
                                    {formatDateTime(screenshot.timestamp)}
                                  </div>
                                  <div className="flex gap-1">
                                    {!screenshot.synced && (
                                      <div className="bg-amber-500/10 text-amber-500 rounded-full px-2 py-0.5 text-[10px]">
                                        Not synced
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </DialogTrigger>
                      <DialogContent className="max-w-4xl p-0 overflow-hidden rounded-2xl bg-[#0F172A] border-[#1E293B] shadow-2xl">
                        <div className="relative">
                          <div className="absolute top-2 right-2 z-10 flex gap-2">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="rounded-full bg-black/20 backdrop-blur-sm hover:bg-black/40 text-white"
                            >
                              <Download size={16} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="rounded-full bg-black/20 backdrop-blur-sm hover:bg-black/40 text-white"
                            >
                              <Share2 size={16} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="rounded-full bg-black/20 backdrop-blur-sm hover:bg-black/40 text-white"
                            >
                              <Trash2 size={16} />
                            </Button>
                            <DialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="rounded-full bg-black/20 backdrop-blur-sm hover:bg-black/40 text-white"
                              >
                                <X size={16} />
                              </Button>
                            </DialogTrigger>
                          </div>
                          <div className="relative aspect-video">
                            <Image
                              src={screenshotsApi.getScreenshotUrl(screenshot.id) || "/placeholder.svg"}
                              alt={`Screenshot from ${formatDateTime(screenshot.timestamp)}`}
                              fill
                              className="object-contain"
                            />
                          </div>
                        </div>
                        <div className="p-4 bg-[#1E293B]">
                          <div className="flex items-center justify-between">
                            <div className="text-sm text-gray-300">
                              Captured at {formatDateTime(screenshot.timestamp)}
                            </div>
                            {!screenshot.synced && (
                              <div className="bg-amber-500/10 text-amber-500 rounded-full px-2.5 py-0.5 text-xs font-medium">
                                Not synced
                              </div>
                            )}
                          </div>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

