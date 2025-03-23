"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import * as screenshotsApi from "@/api/screenshots"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog"
import { formatDateTime } from "@/lib/utils"
import { Camera, Clock, X, Download, Share2, Trash2 } from "lucide-react"
import { motion } from "framer-motion"

interface Screenshot {
  id: string
  timestamp: string
  filepath: string
  thumbnail_path: string
  time_entry_id?: string
  synced: boolean
}

export default function ScreenshotGallery() {
  const [screenshots, setScreenshots] = useState<Screenshot[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedScreenshot, setSelectedScreenshot] = useState<Screenshot | null>(null)

  useEffect(() => {
    const fetchScreenshots = async () => {
      try {
        const { data } = await screenshotsApi.getScreenshots(20, 0)
        setScreenshots(data.screenshots || [])
      } catch (err) {
        console.error("Error fetching screenshots:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchScreenshots()
  }, [])

  const captureScreenshot = async () => {
    try {
      await screenshotsApi.captureScreenshot()
      // Refresh screenshots
      const { data } = await screenshotsApi.getScreenshots(20, 0)
      setScreenshots(data.screenshots || [])
    } catch (err) {
      console.error("Error capturing screenshot:", err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin">
            <Camera className="h-8 w-8 text-gray-500" />
          </div>
          <p className="text-gray-400">Loading screenshots...</p>
        </div>
      </div>
    )
  }

  if (screenshots.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center gap-3">
          <Camera className="h-12 w-12 text-gray-500/50" />
          <p className="text-gray-400">No screenshots found</p>
          <Button
            onClick={captureScreenshot}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5 mt-2"
          >
            <Camera className="mr-2 h-4 w-4" />
            Capture Screenshot
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-white">Screenshots</h3>
        <Button
          onClick={captureScreenshot}
          className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5"
        >
          <Camera className="mr-2 h-4 w-4" />
          Capture Screenshot
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {screenshots.map((screenshot, index) => (
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
                    <div className="text-sm text-gray-300">Captured at {formatDateTime(screenshot.timestamp)}</div>
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
    </div>
  )
}

