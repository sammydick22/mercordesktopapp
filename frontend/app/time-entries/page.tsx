"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/auth-context"
import { useTimeTracking } from "@/context/time-tracking-context"
import { useProjects } from "@/context/projects-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DatePicker } from "@/components/ui/date-picker"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Clock, Search, Filter, Download, Edit, Trash2, MoreHorizontal, RefreshCw, Play } from "lucide-react"
import { motion } from "framer-motion"
import { formatDateTime, formatDuration } from "@/lib/utils"
import * as exportApi from "@/api/export"

export default function TimeEntriesPage() {
  const { user, loading: authLoading } = useAuth()
  const { recentEntries, loading: entriesLoading, loadRecentEntries } = useTimeTracking()
  const { activeProjects } = useProjects()
  const [searchQuery, setSearchQuery] = useState("")
  const [filterStartDate, setFilterStartDate] = useState<Date | undefined>(undefined)
  const [filterEndDate, setFilterEndDate] = useState<Date | undefined>(undefined)
  const [filterProject, setFilterProject] = useState<string | undefined>(undefined)
  const [showFilters, setShowFilters] = useState(false)
  const [showExport, setShowExport] = useState(false)
  const [exportFormat, setExportFormat] = useState<"csv" | "xlsx" | "pdf">("csv")
  const [exportLoading, setExportLoading] = useState(false)
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login")
    }
  }, [user, authLoading, router])

  useEffect(() => {
    loadRecentEntries(100)
  }, [])

  const filteredEntries = recentEntries.filter((entry) => {
    // Search filter
    const matchesSearch =
      !searchQuery || (entry.description && entry.description.toLowerCase().includes(searchQuery.toLowerCase()))

    // Date filters
    const entryDate = new Date(entry.start_time)
    const matchesStartDate = !filterStartDate || entryDate >= filterStartDate
    const matchesEndDate = !filterEndDate || entryDate <= filterEndDate

    // Project filter
    const matchesProject = !filterProject || entry.project_id === filterProject

    return matchesSearch && matchesStartDate && matchesEndDate && matchesProject
  })

  const handleExport = async () => {
    setExportLoading(true)
    try {
      const response = await exportApi.exportTimeEntries({
        format: exportFormat,
        start_date: filterStartDate?.toISOString(),
        end_date: filterEndDate?.toISOString(),
        project_id: filterProject,
        include_screenshots: true,
      })

      // Create a download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement("a")
      link.href = url

      // Set filename based on format
      const date = new Date().toISOString().split("T")[0]
      link.setAttribute("download", `timetracker-export-${date}.${exportFormat}`)

      document.body.appendChild(link)
      link.click()
      link.remove()

      setShowExport(false)
    } catch (err) {
      console.error("Error exporting time entries:", err)
    } finally {
      setExportLoading(false)
    }
  }

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
          Time Entries
        </h1>
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search entries..."
              className="pl-10 bg-[#1E293B] border-[#2D3748] text-white w-[250px]"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <Dialog open={showFilters} onOpenChange={setShowFilters}>
            <DialogTrigger asChild>
              <Button variant="outline" className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]">
                <Filter className="mr-2 h-4 w-4" />
                Filter
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-[#0F172A] border-[#1E293B] text-white">
              <DialogHeader>
                <DialogTitle>Filter Time Entries</DialogTitle>
                <DialogDescription className="text-gray-400">
                  Narrow down your time entries by date range and project.
                </DialogDescription>
              </DialogHeader>
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

                <div className="space-y-2">
                  <Label htmlFor="project">Project</Label>
                  <Select value={filterProject} onValueChange={setFilterProject}>
                    <SelectTrigger id="project" className="bg-[#1E293B] border-[#2D3748] text-white">
                      <SelectValue placeholder="All Projects" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#0F172A] border-[#1E293B]">
                      <SelectItem value="" className="text-white hover:bg-[#1E293B]">
                        All Projects
                      </SelectItem>
                      {activeProjects.map((project) => (
                        <SelectItem key={project.id} value={project.id} className="text-white hover:bg-[#1E293B]">
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter className="flex justify-between">
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
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={showExport} onOpenChange={setShowExport}>
            <DialogTrigger asChild>
              <Button variant="outline" className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]">
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-[#0F172A] border-[#1E293B] text-white">
              <DialogHeader>
                <DialogTitle>Export Time Entries</DialogTitle>
                <DialogDescription className="text-gray-400">
                  Export your time entries to a file format of your choice.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="format">Export Format</Label>
                  <Select
                    value={exportFormat}
                    onValueChange={(value: "csv" | "xlsx" | "pdf") => setExportFormat(value)}
                  >
                    <SelectTrigger id="format" className="bg-[#1E293B] border-[#2D3748] text-white">
                      <SelectValue placeholder="Select format" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#0F172A] border-[#1E293B]">
                      <SelectItem value="csv" className="text-white hover:bg-[#1E293B]">
                        CSV
                      </SelectItem>
                      <SelectItem value="xlsx" className="text-white hover:bg-[#1E293B]">
                        Excel (XLSX)
                      </SelectItem>
                      <SelectItem value="pdf" className="text-white hover:bg-[#1E293B]">
                        PDF
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="text-sm text-gray-400">
                  <p>Current filters will be applied to the export:</p>
                  <ul className="list-disc list-inside mt-2">
                    {filterStartDate && <li>From: {filterStartDate.toLocaleDateString()}</li>}
                    {filterEndDate && <li>To: {filterEndDate.toLocaleDateString()}</li>}
                    {filterProject && <li>Project: {activeProjects.find((p) => p.id === filterProject)?.name}</li>}
                    {searchQuery && <li>Search: "{searchQuery}"</li>}
                  </ul>
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setShowExport(false)}
                  className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleExport}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                  disabled={exportLoading}
                >
                  {exportLoading ? "Exporting..." : "Export"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
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
              <CardTitle className="text-xl font-semibold text-white">Time Entries</CardTitle>
              <CardDescription className="text-gray-400">
                {filteredEntries.length} entries found
                {(filterStartDate || filterEndDate || filterProject || searchQuery) && " (filtered)"}
              </CardDescription>
            </div>
            {(filterStartDate || filterEndDate || filterProject || searchQuery) && (
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
          <CardContent className="p-0">
            {entriesLoading ? (
              <div className="flex justify-center py-8">
                <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
              </div>
            ) : filteredEntries.length === 0 ? (
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
            ) : (
              <Table>
                <TableHeader className="bg-[#1E293B]">
                  <TableRow className="hover:bg-[#1E293B]/50 border-[#2D3748]">
                    <TableHead className="text-gray-300 font-medium">Description</TableHead>
                    <TableHead className="text-gray-300 font-medium">Project</TableHead>
                    <TableHead className="text-gray-300 font-medium">Start Time</TableHead>
                    <TableHead className="text-gray-300 font-medium">End Time</TableHead>
                    <TableHead className="text-gray-300 font-medium">Duration</TableHead>
                    <TableHead className="text-gray-300 font-medium">Status</TableHead>
                    <TableHead className="text-gray-300 font-medium w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEntries.map((entry) => (
                    <TableRow key={entry.id} className="hover:bg-[#1E293B]/50 border-[#2D3748]">
                      <TableCell className="font-medium text-white">{entry.description || "No description"}</TableCell>
                      <TableCell className="text-gray-300">
                        {entry.project_id
                          ? activeProjects.find((p) => p.id === entry.project_id)?.name || "Unknown Project"
                          : "—"}
                      </TableCell>
                      <TableCell className="text-gray-300">{formatDateTime(entry.start_time)}</TableCell>
                      <TableCell className="text-gray-300">
                        {entry.end_time ? formatDateTime(entry.end_time) : "—"}
                      </TableCell>
                      <TableCell className="text-gray-300 font-mono">{formatDuration(entry.duration || 0)}</TableCell>
                      <TableCell>
                        {entry.is_active ? (
                          <Badge className="bg-green-500/10 text-green-500 hover:bg-green-500/20">Active</Badge>
                        ) : !entry.synced ? (
                          <Badge className="bg-amber-500/10 text-amber-500 hover:bg-amber-500/20">Not synced</Badge>
                        ) : (
                          <Badge className="bg-blue-500/10 text-blue-500 hover:bg-blue-500/20">Synced</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8 p-0 hover:bg-[#2D3748]">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-[#0F172A] border-[#1E293B]">
                            <DropdownMenuItem className="hover:bg-[#1E293B] text-gray-300 hover:text-white">
                              <Edit className="mr-2 h-4 w-4" />
                              <span>Edit</span>
                            </DropdownMenuItem>
                            <DropdownMenuItem className="hover:bg-[#1E293B] text-red-400 hover:text-red-300">
                              <Trash2 className="mr-2 h-4 w-4" />
                              <span>Delete</span>
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

