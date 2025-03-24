"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/auth-context"
import { useTimeTracking } from "@/context/time-tracking-context"
import { useProjects } from "@/context/projects-context"
import { useSettings } from "@/context/settings-context"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Play, Pause, Briefcase, ListTodo, Timer } from "lucide-react"
import { formatDuration } from "@/lib/utils"
import { calculateElapsedTime } from "@/lib/timezone-utils"
import TimeEntryList from "@/components/time-entry-list"
import { motion } from "framer-motion"

interface Task {
  id: string
  project_id: string
  name: string
  description?: string
  estimated_hours?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// We're using the calculateElapsedTime function from timezone-utils.ts instead of a local helper

export default function TimeTrackingPage() {
  const { user, loading: authLoading } = useAuth()
  const { currentTimeEntry, recentEntries, startTimeEntry, stopTimeEntry, loading, localStartTime } = useTimeTracking()
  const { activeProjects, getProjectTasks } = useProjects()
  const { profile } = useSettings()
  const [description, setDescription] = useState("")
  const [projectId, setProjectId] = useState<string | undefined>(undefined)
  const [taskId, setTaskId] = useState<string | undefined>(undefined)
  const [projectTasks, setProjectTasks] = useState<Task[]>([])
  const [loadingTasks, setLoadingTasks] = useState(false)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [optimisticTimer, setOptimisticTimer] = useState<number | null>(null)
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login")
    }
  }, [user, authLoading, router])

  useEffect(() => {
    if (currentTimeEntry) {
      setDescription(currentTimeEntry.description || "")
      
      // Set project and task from the current time entry if available
      if (currentTimeEntry.project_id) {
        setProjectId(currentTimeEntry.project_id)
        
        if (currentTimeEntry.task_id) {
          setTaskId(currentTimeEntry.task_id)
        }
      }
    }
  }, [currentTimeEntry])

  // Load tasks when project changes
  useEffect(() => {
    if (projectId) {
      setLoadingTasks(true)
      const loadTasks = async () => {
        try {
          const tasks = await getProjectTasks(projectId)
          setProjectTasks(tasks.filter(task => task.is_active))
        } catch (err) {
          console.error("Error loading tasks:", err)
          setProjectTasks([])
        } finally {
          setLoadingTasks(false)
        }
      }
      loadTasks()
    } else {
      setProjectTasks([])
    }
  }, [projectId, getProjectTasks])

  // Reset task selection when project changes
  useEffect(() => {
    setTaskId(undefined)
  }, [projectId])

  // Timer effect for tracking elapsed time
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null
    
    console.log("[TIMER DEBUG] Timer effect in page.tsx - triggered with:", {
      currentTimeEntry: currentTimeEntry ? {
        id: currentTimeEntry.id,
        is_active: currentTimeEntry.is_active,
        start_time: currentTimeEntry.start_time
      } : null,
      localStartTime,
      optimisticTimer,
      profileTimezone: profile?.timezone
    });

    // For tracking/debugging how long we've been timing
    const manualElapsed = optimisticTimer !== null ? optimisticTimer : 0;

    // Priority 1: Use localStartTime if we have it and we're in the transition period
    // This ensures continuity between optimistic updates and server-confirmed updates
    if (localStartTime) {
      console.log("[TIMER DEBUG] Using localStartTime for consistent timing:", localStartTime);
      
      // This handles both the initial optimistic period and the transition to server state
      interval = setInterval(() => {
        const elapsed = calculateElapsedTime(localStartTime, profile?.timezone);
        console.log("[TIMER DEBUG] Local time interval - elapsed:", elapsed);
        setElapsedTime(elapsed);
      }, 1000);
      
      // Set initial elapsed time immediately
      const initialLocalElapsed = calculateElapsedTime(localStartTime, profile?.timezone);
      console.log("[TIMER DEBUG] Initial local elapsed time:", initialLocalElapsed);
      setElapsedTime(initialLocalElapsed);
    }
    // Priority 2: Use server time entry if we have one
    else if (currentTimeEntry?.is_active && currentTimeEntry.start_time) {
      console.log("[TIMER DEBUG] Using server time entry - start_time:", currentTimeEntry.start_time);
      
      // Clear any remaining optimistic UI state since we're fully on server state now
      setOptimisticTimer(null);
      
      // Start interval to update the elapsed time
      interval = setInterval(() => {
        const elapsed = calculateElapsedTime(currentTimeEntry.start_time, profile?.timezone);
        console.log("[TIMER DEBUG] Server time interval - elapsed:", elapsed, "Manual count:", manualElapsed + 1);
        setElapsedTime(elapsed);
      }, 1000);
      
      // Set initial elapsed time immediately
      const initialElapsed = calculateElapsedTime(currentTimeEntry.start_time, profile?.timezone);
      console.log("[TIMER DEBUG] Initial server elapsed time:", initialElapsed);
      setElapsedTime(initialElapsed);
    } 
    // Priority 3: Handle completed time entries
    else if (currentTimeEntry && !currentTimeEntry.is_active) {
      console.log("[TIMER DEBUG] Inactive time entry - duration:", currentTimeEntry.duration);
      setElapsedTime(currentTimeEntry.duration || 0);
      setOptimisticTimer(null);
    }
    // Priority 4: Use component-level optimistic timer as last resort
    else if (optimisticTimer !== null) {
      console.log("[TIMER DEBUG] Using component optimistic timer:", optimisticTimer);
      
      interval = setInterval(() => {
        setOptimisticTimer(prev => {
          const newValue = prev !== null ? prev + 1 : null;
          console.log("[TIMER DEBUG] Optimistic timer update:", newValue);
          return newValue;
        });
      }, 1000);
    } else {
      console.log("[TIMER DEBUG] No active timer condition matched");
    }

    return () => {
      if (interval) {
        console.log("[TIMER DEBUG] Clearing interval");
        clearInterval(interval);
      }
    }
  }, [currentTimeEntry, localStartTime, optimisticTimer, profile?.timezone])

  const handleStartTracking = async () => {
    // Set optimistic timer immediately for better UX
    setOptimisticTimer(0)
    console.log("[TIMER DEBUG] Page - Start button clicked, setting optimistic timer and calling API");
    
    try {
      await startTimeEntry(projectId, taskId, description)
      // Once startTimeEntry succeeds, we should clear the optimistic timer
      // since we'll be getting a real server entry soon
      setOptimisticTimer(null)
    } catch (error) {
      // If there's an error, clear the optimistic timer
      setOptimisticTimer(null)
      console.error("Failed to start time tracking:", error)
    }
  }

  const handleStopTracking = async () => {
    try {
      await stopTimeEntry(description)
    } catch (error) {
      console.error("Failed to stop time tracking:", error)
    }
  }

  const handleDescriptionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setDescription(e.target.value)
  }

  // Determine which timer value to display
  const displayTime = optimisticTimer !== null ? optimisticTimer : elapsedTime

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
                  {formatDuration(displayTime)}
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
                      disabled={currentTimeEntry?.is_active || optimisticTimer !== null}
                    >
                      <option value="" className="text-gray-400">Select project</option>
                      {activeProjects.length === 0 ? (
                        <option value="" disabled className="text-gray-400">No projects available</option>
                      ) : (
                        activeProjects.map((project) => (
                          <option key={project.id} value={project.id} className="text-white">
                            {project.name}
                          </option>
                        ))
                      )}
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
                      disabled={currentTimeEntry?.is_active || !projectId || loadingTasks || optimisticTimer !== null}
                    >
                      {loadingTasks ? (
                        <option value="" className="text-gray-400">Loading tasks...</option>
                      ) : !projectId ? (
                        <option value="" className="text-gray-400">Select a project first</option>
                      ) : projectTasks.length === 0 ? (
                        <option value="" className="text-gray-400">No tasks available</option>
                      ) : (
                        <>
                          <option value="" className="text-gray-400">Select task</option>
                          {projectTasks.map((task) => (
                            <option key={task.id} value={task.id} className="text-white">
                              {task.name}
                            </option>
                          ))}
                        </>
                      )}
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
              {currentTimeEntry?.is_active || optimisticTimer !== null ? (
                <Button
                  variant="destructive"
                  size="lg"
                  onClick={handleStopTracking}
                  disabled={loading || optimisticTimer !== null}
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
