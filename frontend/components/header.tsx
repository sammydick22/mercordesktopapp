"use client"

import { useAuth } from "@/context/auth-context"
import { useTimeTracking } from "@/context/time-tracking-context"
import { useSync } from "@/context/sync-context"
import { useSettings } from "@/context/settings-context"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Play, Pause, RefreshCw, AlertCircle, Bell, Moon, Sun, User, LogOut } from "lucide-react"
import { formatDuration } from "@/lib/utils"
import { calculateElapsedTime } from "@/lib/timezone-utils"
import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"
import { usePathname } from "next/navigation"

export default function Header() {
  const { user, logout } = useAuth()
  const { currentTimeEntry, startTimeEntry, stopTimeEntry, localStartTime } = useTimeTracking()
  const { syncStatus, syncAll } = useSync()
  const { profile } = useSettings()
  const [elapsedTime, setElapsedTime] = useState(0)
  const [optimisticTimer, setOptimisticTimer] = useState<number | null>(null)
  const [isDark, setIsDark] = useState(true)
  const pathname = usePathname()

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    console.log("[TIMER DEBUG] Header timer effect triggered with:", {
      currentTimeEntry: currentTimeEntry ? {
        id: currentTimeEntry.id,
        is_active: currentTimeEntry.is_active,
        start_time: currentTimeEntry.start_time
      } : null,
      localStartTime,
      optimisticTimer,
      profileTimezone: profile?.timezone
    });

    // For tracking/debugging purposes
    const manualElapsed = optimisticTimer !== null ? optimisticTimer : 0;
    
    // Priority 1: Use localStartTime if available for consistency during transitions
    if (localStartTime) {
      console.log("[TIMER DEBUG] Header - Using localStartTime for consistent timing:", localStartTime);
      
      // Clear component-level optimistic timer since we're using the context-level localStartTime
      setOptimisticTimer(null);
      
      // Start interval using the reliable localStartTime
      interval = setInterval(() => {
        const elapsed = calculateElapsedTime(localStartTime, profile?.timezone);
        console.log("[TIMER DEBUG] Header local time interval - elapsed:", elapsed);
        setElapsedTime(elapsed);
      }, 1000);
      
      // Set initial elapsed time immediately
      const initialLocalElapsed = calculateElapsedTime(localStartTime, profile?.timezone);
      console.log("[TIMER DEBUG] Header initial local elapsed time:", initialLocalElapsed);
      setElapsedTime(initialLocalElapsed);
    }
    // Priority 2: Use server time entry when available
    else if (currentTimeEntry?.is_active && currentTimeEntry.start_time) {
      console.log("[TIMER DEBUG] Header - Using server time entry:", currentTimeEntry.start_time);
      
      // Clear any optimistic timer
      setOptimisticTimer(null);
      
      // Start interval to update the elapsed time
      interval = setInterval(() => {
        const elapsed = calculateElapsedTime(currentTimeEntry.start_time, profile?.timezone);
        console.log("[TIMER DEBUG] Header server interval - elapsed:", elapsed, "Manual count:", manualElapsed + 1);
        setElapsedTime(elapsed);
      }, 1000);
      
      // Set initial elapsed time immediately
      const initialElapsed = calculateElapsedTime(currentTimeEntry.start_time, profile?.timezone);
      console.log("[TIMER DEBUG] Header initial server elapsed time:", initialElapsed);
      setElapsedTime(initialElapsed);
    } 
    // Priority 3: Handle completed time entries
    else if (currentTimeEntry && !currentTimeEntry.is_active) {
      console.log("[TIMER DEBUG] Header - Inactive time entry - duration:", currentTimeEntry.duration);
      setElapsedTime(currentTimeEntry.duration || 0);
      setOptimisticTimer(null);
    }
    // Priority 4: Use component-level optimistic timer as last resort
    else if (optimisticTimer !== null) {
      console.log("[TIMER DEBUG] Header - Using component optimistic timer:", optimisticTimer);
      
      interval = setInterval(() => {
        setOptimisticTimer(prev => {
          const newValue = prev !== null ? prev + 1 : null;
          console.log("[TIMER DEBUG] Header optimistic timer update:", newValue);
          return newValue;
        });
      }, 1000);
    } else {
      console.log("[TIMER DEBUG] Header - No timer conditions matched");
    }

    return () => {
      if (interval) {
        console.log("[TIMER DEBUG] Header - Clearing interval");
        clearInterval(interval);
      }
    }
  }, [currentTimeEntry, optimisticTimer, localStartTime, profile?.timezone])

  const toggleTheme = () => {
    const html = document.querySelector("html")
    if (html?.classList.contains("dark")) {
      html.classList.remove("dark")
      setIsDark(false)
    } else {
      html?.classList.add("dark")
      setIsDark(true)
    }
  }

  if (!user || pathname === "/login") return null

  return (
    <header className="bg-[#0F172A] border-b border-[#1E293B] p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {currentTimeEntry?.is_active || optimisticTimer !== null || localStartTime ? (
            <>
              <Button
                onClick={() => stopTimeEntry()}
                disabled={optimisticTimer !== null && !currentTimeEntry?.is_active}
                className="bg-red-600 hover:bg-red-700 text-white font-medium rounded-full px-6 py-2.5 flex items-center gap-2"
              >
                <Pause size={16} />
                Stop
              </Button>
              <div className="font-mono text-6xl font-bold tabular-nums text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600">
                {formatDuration(optimisticTimer !== null ? optimisticTimer : elapsedTime)}
              </div>
              <div className="text-sm text-gray-400 max-w-md truncate">
                {currentTimeEntry?.description || "No description"}
              </div>
            </>
          ) : (
            <Button
              onClick={() => {
                // Set optimistic timer immediately
                setOptimisticTimer(0);
                console.log("[TIMER DEBUG] Header - Start button clicked, setting optimistic timer");
                // Then call the API
                startTimeEntry();
              }}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5 flex items-center gap-2"
            >
              <Play size={16} />
              Start Tracking
            </Button>
          )}
        </div>

        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="icon"
            onClick={() => syncAll()}
            disabled={syncStatus?.is_syncing}
            className="rounded-full w-10 h-10 border-[#1E293B] hover:bg-[#1E293B] bg-transparent"
          >
            <RefreshCw size={18} className={cn(syncStatus?.is_syncing && "animate-spin")} />
          </Button>

          {syncStatus?.sync_error && (
            <div className="bg-amber-500/10 text-amber-500 rounded-full px-2.5 py-0.5 text-xs font-medium flex items-center gap-1">
              <AlertCircle size={14} />
              <span>Sync error</span>
            </div>
          )}

          <Button
            variant="outline"
            size="icon"
            className="rounded-full w-10 h-10 border-[#1E293B] hover:bg-[#1E293B] bg-transparent"
          >
            <Bell size={18} />
          </Button>

          <Button
            variant="outline"
            size="icon"
            onClick={toggleTheme}
            className="rounded-full w-10 h-10 border-[#1E293B] hover:bg-[#1E293B] bg-transparent"
          >
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full w-10 h-10 p-0">
                <Avatar className="h-10 w-10 border border-[#1E293B]">
                  <AvatarImage src={`https://avatar.vercel.sh/${user.email}`} />
                  <AvatarFallback className="bg-[#1E293B]">{user.email.substring(0, 2).toUpperCase()}</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 bg-[#0F172A] border-[#1E293B]">
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none text-white">{user.email}</p>
                  <p className="text-xs leading-none text-gray-400">{user.id}</p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-[#1E293B]" />
              <DropdownMenuItem className="hover:bg-[#1E293B] text-gray-300 hover:text-white">
                <User className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </DropdownMenuItem>
              <DropdownMenuItem className="hover:bg-[#1E293B] text-gray-300 hover:text-white" onClick={() => logout()}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
