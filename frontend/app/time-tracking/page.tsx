"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/auth-context"
import { useTimeTracking } from "@/context/time-tracking-context"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Play, Pause, Briefcase, ListTodo, Timer } from "lucide-react"
import { formatDuration } from "@/lib/utils"
import TimeEntryList from "@/components/time-entry-list"
import { motion } from "framer-motion"

export default function TimeTrackingPage() {
  const { user, loading: authLoading } = useAuth()
  const { currentTimeEntry, recentEntries, startTimeEntry, stopTimeEntry, loading } = useTimeTracking()
  const [description, setDescription] = useState("")
  const [projectId, setProjectId] = useState<string | undefined>(undefined)
  const [taskId, setTaskId] = useState<string | undefined>(undefined)
  const [elapsedTime, setElapsedTime] = useState(0)
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login")
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (currentTimeEntry) {
      setDescription(currentTimeEntry.description || "")
    }
  }, [currentTimeEntry])

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    if (currentTimeEntry?.is_active) {
      const startTime = new Date(currentTimeEntry.start_time).getTime()

      interval = setInterval(() => {
        const now = Date.now()
        const duration = Math.floor((now - startTime) / 1000)
        setElapsedTime(duration)
      }, 1000)
    } else {
      setElapsedTime(currentTimeEntry?.duration || 0)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [currentTimeEntry])

  const handleStartTracking = async () => {
    await startTimeEntry(projectId, taskId, description)
  }

  const handleStopTracking = async () => {
    await stopTimeEntry(description)
  }

  const handleDescriptionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setDescription(e.target.value)
  }

  if (authLoading || !user) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-4">
          <div className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600 text-2xl font-bold">
            TimeTracker
          </div>
          <div className="animate-spin">
            <Timer size={24} />
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
        Time Tracking
      </motion.h1>

      <div className="grid gap-6 md:grid-cols-2">
        <motion.div
          className="md:col-span-2"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
            <CardHeader className="p-6">
              <CardTitle className="text-2xl font-semibold text-white">Current Time Entry</CardTitle>
              <CardDescription className="text-gray-400">Track time for your current task</CardDescription>
            </CardHeader>
            <CardContent className="p-6 pt-0 space-y-6">
              <div className="flex items-center justify-center">
                <div className="font-mono text-7xl font-bold tabular-nums text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600">
                  {formatDuration(elapsedTime)}
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="project" className="text-sm font-medium text-gray-400 flex items-center gap-2">
                      <Briefcase className="h-4 w-4" />
                      Project
                    </Label>
                    <select
                      id="project"
                      className="flex h-10 w-full rounded-md border px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm bg-[#1E293B] border-[#2D3748] text-white"
                      value={projectId || ""}
                      onChange={(e) => setProjectId(e.target.value === "" ? undefined : e.target.value)}
                      disabled={currentTimeEntry?.is_active}
                    >
                      <option value="" className="text-gray-400">Select project</option>
                      <option value="project1" className="text-white">Project 1</option>
                      <option value="project2" className="text-white">Project 2</option>
                      <option value="project3" className="text-white">Project 3</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="task" className="text-sm font-medium text-gray-400 flex items-center gap-2">
                      <ListTodo className="h-4 w-4" />
                      Task
                    </Label>
                    <select
                      id="task"
                      className="flex h-10 w-full rounded-md border px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm bg-[#1E293B] border-[#2D3748] text-white"
                      value={taskId || ""}
                      onChange={(e) => setTaskId(e.target.value === "" ? undefined : e.target.value)}
                      disabled={currentTimeEntry?.is_active}
                    >
                      <option value="" className="text-gray-400">Select task</option>
                      <option value="task1" className="text-white">Task 1</option>
                      <option value="task2" className="text-white">Task 2</option>
                      <option value="task3" className="text-white">Task 3</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description" className="text-sm font-medium text-gray-400">
                    Description
                  </Label>
                  <Textarea
                    id="description"
                    placeholder="What are you working on?"
                    value={description}
                    onChange={handleDescriptionChange}
                    rows={3}
                    className="bg-[#1E293B] border-[#2D3748] text-white resize-none"
                  />
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex items-center p-6 pt-0 justify-center">
              {currentTimeEntry?.is_active ? (
                <Button
                  variant="destructive"
                  size="lg"
                  onClick={handleStopTracking}
                  disabled={loading}
                  className="bg-red-600 hover:bg-red-700 text-white font-medium rounded-full px-6 py-2.5 w-full max-w-md"
                >
                  <Pause className="mr-2 h-4 w-4" />
                  Stop Tracking
                </Button>
              ) : (
                <Button
                  variant="default"
                  size="lg"
                  onClick={handleStartTracking}
                  disabled={loading}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5 w-full max-w-md"
                >
                  <Play className="mr-2 h-4 w-4" />
                  Start Tracking
                </Button>
              )}
            </CardFooter>
          </Card>
        </motion.div>

        <motion.div
          className="md:col-span-2"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
            <CardHeader className="p-6">
              <CardTitle className="text-2xl font-semibold text-white">Recent Time Entries</CardTitle>
              <CardDescription className="text-gray-400">Your most recent tracked time</CardDescription>
            </CardHeader>
            <CardContent className="p-6 pt-0">
              <TimeEntryList entries={recentEntries} />
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
