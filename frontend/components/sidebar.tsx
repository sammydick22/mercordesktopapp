"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Clock, LayoutDashboard, ImageIcon, Settings, BarChart, Folder, Users, ChevronRight } from "lucide-react"
import { useAuth } from "@/context/auth-context"
import { motion } from "framer-motion"

export default function Sidebar() {
  const pathname = usePathname()
  const { user } = useAuth()
  const [collapsed, setCollapsed] = useState(false)
  const [hoveredItem, setHoveredItem] = useState<string | null>(null)

  const toggleSidebar = () => setCollapsed(!collapsed)

  const navItems = [
    {
      name: "Dashboard",
      href: "/",
      icon: LayoutDashboard,
    },
    {
      name: "Time Tracking",
      href: "/time-tracking",
      icon: Clock,
    },
    {
      name: "Time Entries",
      href: "/time-entries",
      icon: BarChart,
    },
    {
      name: "Screenshots",
      href: "/screenshots",
      icon: ImageIcon,
    },
    {
      name: "Projects",
      href: "/projects",
      icon: Folder,
    },
    {
      name: "Clients",
      href: "/clients",
      icon: Users,
    },
    {
      name: "Settings",
      href: "/settings",
      icon: Settings,
    },
  ]

  if (!user && pathname !== "/login") return null

  return (
    <div
      className={cn(
        "bg-[#0F172A] border-r border-[#1E293B] h-screen transition-all duration-300 flex flex-col",
        collapsed ? "w-20" : "w-72",
        pathname === "/login" && "hidden",
      )}
    >
      <div className="flex items-center justify-between p-5 border-b border-[#1E293B]">
        {!collapsed && <h1 className="text-xl font-bold premium-text-gradient">TimeTracker</h1>}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className={cn("ml-auto rounded-full w-8 h-8 hover:bg-[#1E293B]", collapsed ? "rotate-0" : "rotate-180")}
        >
          <ChevronRight size={18} />
        </Button>
      </div>
      <nav className="flex-1 py-6 px-3">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onMouseEnter={() => setHoveredItem(item.href)}
                  onMouseLeave={() => setHoveredItem(null)}
                >
                  <div
                    className={cn(
                      "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 hover:bg-[#1E293B]",
                      isActive && "bg-blue-600/10 text-blue-500",
                    )}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="activeIndicator"
                        className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 rounded-r-full"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.2 }}
                      />
                    )}
                    <item.icon
                      size={20}
                      className={cn(
                        "transition-all",
                        isActive ? "text-blue-500" : "text-gray-400",
                        hoveredItem === item.href && !isActive && "text-white",
                      )}
                    />
                    {!collapsed && (
                      <span
                        className={cn(
                          "transition-all",
                          isActive ? "text-blue-500" : "text-gray-400",
                          hoveredItem === item.href && !isActive && "text-white",
                        )}
                      >
                        {item.name}
                      </span>
                    )}
                  </div>
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>
      <div className="p-4 border-t border-[#1E293B]">
        {!collapsed && (
          <div className="text-xs text-gray-400 space-y-1">
            <div className="flex items-center justify-between">
              <p>Version 1.0.0</p>
              <div className="bg-green-500/10 text-green-500 rounded-full px-2 py-0.5 text-xs">Online</div>
            </div>
            <p>Last synced: {new Date().toLocaleTimeString()}</p>
          </div>
        )}
      </div>
    </div>
  )
}

