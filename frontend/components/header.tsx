"use client"

import { useAuth } from "@/context/auth-context"
import { useTimeTracking } from "@/context/time-tracking-context"
import { useSync } from "@/context/sync-context"
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
import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"
import { usePathname } from "next/navigation"

export default function Header() {
  const { user, logout } = useAuth()
  const { currentTimeEntry, startTimeEntry, stopTimeEntry } = useTimeTracking()
  const { syncStatus, syncAll } = useSync()
  const [elapsedTime, setElapsedTime] = useState(0)
  const [isDark, setIsDark] = useState(true)
  const pathname = usePathname()

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
          {currentTimeEntry?.is_active ? (
            <>
              <Button
                onClick={() => stopTimeEntry()}
                className="bg-red-600 hover:bg-red-700 text-white font-medium rounded-full px-6 py-2.5 flex items-center gap-2"
              >
                <Pause size={16} />
                Stop
              </Button>
              <div className="font-mono text-6xl font-bold tabular-nums text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600">
                {formatDuration(elapsedTime)}
              </div>
              <div className="text-sm text-gray-400 max-w-md truncate">
                {currentTimeEntry.description || "No description"}
              </div>
            </>
          ) : (
            <Button
              onClick={() => startTimeEntry()}
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

