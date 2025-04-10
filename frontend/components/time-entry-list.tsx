"use client"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { formatDateTime, formatDuration, cn } from "@/lib/utils"
import { Clock, Edit, Trash2, Play, MoreHorizontal } from "lucide-react"
import { motion } from "framer-motion"

// Import primitive components directly for custom dropdowns
import * as React from "react"
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu"

// Complete set of custom Dropdown Menu components with simplified animations
const SimpleDropdownMenu = DropdownMenuPrimitive.Root
SimpleDropdownMenu.displayName = "SimpleDropdownMenu"

const SimpleDropdownMenuTrigger = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Trigger
    ref={ref}
    className={cn("outline-none", className)}
    {...props}
  />
))
SimpleDropdownMenuTrigger.displayName = "SimpleDropdownMenuTrigger"

const SimpleDropdownMenuContent = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        "z-50 min-w-[8rem] overflow-hidden rounded-md border p-1 shadow-md",
        className
      )}
      style={{ 
        opacity: 1,
        pointerEvents: "auto",
        transform: "translateY(0)",
        transition: "none" 
      }}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
))
SimpleDropdownMenuContent.displayName = "SimpleDropdownMenuContent"

const SimpleDropdownMenuItem = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none",
      className
    )}
    style={{ pointerEvents: "auto" }}
    {...props}
  />
))
SimpleDropdownMenuItem.displayName = "SimpleDropdownMenuItem"

interface TimeEntry {
  id: string
  start_time: string
  end_time?: string
  duration?: number
  project_id?: string
  task_id?: string
  description?: string
  is_active: boolean
  synced: boolean
}

interface TimeEntryListProps {
  entries: TimeEntry[]
}

export default function TimeEntryList({ entries }: TimeEntryListProps) {
  if (entries.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <div className="flex flex-col items-center gap-3">
          <Clock className="h-12 w-12 text-gray-500/50" />
          <p>No time entries found</p>
          <Button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5 mt-2">
            <Play className="mr-2 h-4 w-4" />
            Start Tracking
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {entries.map((entry, index) => (
        <motion.div
          key={entry.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: index * 0.05 }}
        >
          <TimeEntryCard entry={entry} />
        </motion.div>
      ))}
    </div>
  )
}

function TimeEntryCard({ entry }: { entry: TimeEntry }) {
  return (
    <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden hover:bg-[#1E293B]/50 transition-all duration-300">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="font-medium text-white">{entry.description || "No description"}</div>
            <div className="text-sm text-gray-400 flex items-center">
              <Clock className="mr-1 h-3 w-3" />
              {formatDateTime(entry.start_time)}
              {entry.end_time && ` - ${formatDateTime(entry.end_time)}`}
            </div>
            <div className="flex flex-wrap gap-2">
              {entry.project_id && (
                <div className="bg-blue-500/10 text-blue-500 rounded-full px-2.5 py-0.5 text-xs font-medium">
                  Project
                </div>
              )}
              {entry.task_id && (
                <div className="bg-blue-500/10 text-blue-500 rounded-full px-2.5 py-0.5 text-xs font-medium">Task</div>
              )}
              {!entry.synced && (
                <div className="bg-amber-500/10 text-amber-500 rounded-full px-2.5 py-0.5 text-xs font-medium">
                  Not synced
                </div>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end space-y-2">
            <div className="text-lg font-mono font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600">
              {formatDuration(entry.duration || 0)}
            </div>
            <div className="flex space-x-1">
              <SimpleDropdownMenu>
                <SimpleDropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="rounded-full h-8 w-8 hover:bg-[#2D3748]">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </SimpleDropdownMenuTrigger>
                <SimpleDropdownMenuContent align="end" className="bg-[#0F172A] border-[#1E293B]">
                  <SimpleDropdownMenuItem className="hover:bg-[#1E293B] text-gray-300 hover:text-white">
                    <Edit className="mr-2 h-4 w-4" />
                    <span>Edit</span>
                  </SimpleDropdownMenuItem>
                  <SimpleDropdownMenuItem className="hover:bg-[#1E293B] text-red-400 hover:text-red-300">
                    <Trash2 className="mr-2 h-4 w-4" />
                    <span>Delete</span>
                  </SimpleDropdownMenuItem>
                </SimpleDropdownMenuContent>
              </SimpleDropdownMenu>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
