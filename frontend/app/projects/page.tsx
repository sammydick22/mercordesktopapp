"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/auth-context"
import { useProjects } from "@/context/projects-context"
import { useClients } from "@/context/clients-context"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Briefcase, Plus, Search, Edit, Trash2, MoreHorizontal, RefreshCw, ListTodo, X } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { motion } from "framer-motion"
import { formatDate, cn } from "@/lib/utils"

// React component to define DialogContent
import * as React from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"

// Custom Dialog components with simplified animations
const SimpleDialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-black/80 opacity-100 transition-opacity",
      className
    )}
    {...props}
  />
))
SimpleDialogOverlay.displayName = "SimpleDialogOverlay"

const SimpleDialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPrimitive.Portal>
    <SimpleDialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border p-6 shadow-lg sm:rounded-lg opacity-100 transition-opacity",
        className
      )}
      style={{ transform: "translate(-50%, -50%)" }}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
))
SimpleDialogContent.displayName = "SimpleDialogContent"

export default function ProjectsPage() {
  const { user, loading: authLoading } = useAuth()
  const { projects, activeProjects, loading: projectsLoading, error, fetchProjects, createProject } = useProjects()
  const { activeClients } = useClients()
  const [searchQuery, setSearchQuery] = useState("")
  const [showAddProject, setShowAddProject] = useState(false)
  const [showProjectTasks, setShowProjectTasks] = useState<string | null>(null)
  const [newProject, setNewProject] = useState({
    name: "",
    client_id: "",
    description: "",
    color: "#3b82f6",
    hourly_rate: 0,
    is_billable: true,
  })
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login")
    }
  }, [user, authLoading, router])

  const filteredProjects = projects.filter(
    (project) =>
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (project.client_name && project.client_name.toLowerCase().includes(searchQuery.toLowerCase())),
  )

  const handleCreateProject = async () => {
    try {
      await createProject(newProject)
      setShowAddProject(false)
      setNewProject({
        name: "",
        client_id: "",
        description: "",
        color: "#3b82f6",
        hourly_rate: 0,
        is_billable: true,
      })
      
      // Add a slight delay before fetching projects to ensure database has completed the operation
      setTimeout(() => {
        fetchProjects()
      }, 500)
    } catch (err) {
      console.error("Error creating project:", err)
    }
  }

  // Use a custom dialog open handler with setTimeout to ensure the DOM is ready
  const handleOpenDialog = () => {
    // Force the action to occur on the next event loop tick
    setTimeout(() => {
      setShowAddProject(true)
    }, 10) // Increase timeout slightly
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
          Projects
        </h1>
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search projects..."
              className="pl-10 bg-[#1E293B] border-[#2D3748] text-white w-[250px]"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Button 
            onClick={handleOpenDialog}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5"
          >
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
          
          {/* Fixed dialog that doesn't use DialogTrigger */}
          <Dialog open={showAddProject} onOpenChange={setShowAddProject}>
            <SimpleDialogContent className="bg-[#0F172A] border-[#1E293B] text-white" style={{ pointerEvents: "auto" }}>
              <DialogHeader>
                <DialogTitle>Create New Project</DialogTitle>
                <DialogDescription className="text-gray-400">
                  Add a new project to track time against.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Project Name</Label>
                  <Input
                    id="name"
                    placeholder="Enter project name"
                    className="bg-[#1E293B] border-[#2D3748] text-white"
                    value={newProject.name}
                    onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                    autoComplete="off"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="client">Client</Label>
                  <Select
                    value={newProject.client_id}
                    onValueChange={(value) => setNewProject({ ...newProject, client_id: value })}
                  >
                    <SelectTrigger id="client" className="bg-[#1E293B] border-[#2D3748] text-white">
                      <SelectValue placeholder="Select client" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#0F172A] border-[#1E293B]">
                      {activeClients.map((client) => (
                        <SelectItem key={client.id} value={client.id} className="text-white hover:bg-[#1E293B]">
                          {client.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Project description"
                    className="bg-[#1E293B] border-[#2D3748] text-white resize-none"
                    value={newProject.description}
                    onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="color">Color</Label>
                    <div className="flex items-center gap-2">
                      <div
                        className="w-8 h-8 rounded-full border border-[#2D3748]"
                        style={{ backgroundColor: newProject.color }}
                      />
                      <Input
                        type="color"
                        id="color"
                        className="w-12 h-8 p-0 bg-transparent border-0"
                        value={newProject.color}
                        onChange={(e) => setNewProject({ ...newProject, color: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="hourly_rate">Hourly Rate ($)</Label>
                    <Input
                      id="hourly_rate"
                      type="number"
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                      value={newProject.hourly_rate}
                      onChange={(e) => setNewProject({ ...newProject, hourly_rate: Number.parseFloat(e.target.value) })}
                      autoComplete="off"
                    />
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="is_billable"
                    checked={newProject.is_billable}
                    onCheckedChange={(checked) => setNewProject({ ...newProject, is_billable: checked })}
                  />
                  <Label htmlFor="is_billable">Billable Project</Label>
                </div>
              </div>
              <DialogFooter>
                <DialogClose asChild>
                  <Button
                    variant="outline"
                    className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
                  >
                    Cancel
                 </Button>
                </DialogClose>
                <DialogClose asChild>
                  <Button
                    onClick={handleCreateProject}
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                    disabled={!newProject.name}
                  >
                    Create Project
                  </Button>
                </DialogClose>
              </DialogFooter>
              </SimpleDialogContent>
          </Dialog>
        </div>
      </motion.div>

      <Tabs defaultValue="all" className="relative">
        <TabsList className="inline-flex h-10 items-center justify-center rounded-lg bg-[#1E293B] p-1 text-gray-400">
          <TabsTrigger
            value="all"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-[#0F172A] data-[state=active]:text-white data-[state=active]:shadow-sm"
          >
            All Projects
          </TabsTrigger>
          <TabsTrigger
            value="active"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-[#0F172A] data-[state=active]:text-white data-[state=active]:shadow-sm"
          >
            Active Projects
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-4">
          <ProjectsTable
            projects={filteredProjects}
            showProjectTasks={showProjectTasks}
            setShowProjectTasks={setShowProjectTasks}
            handleOpenParentDialog={handleOpenDialog}
          />
        </TabsContent>

        <TabsContent value="active" className="mt-4">
          <ProjectsTable
            projects={filteredProjects.filter((p) => p.is_active)}
            showProjectTasks={showProjectTasks}
            setShowProjectTasks={setShowProjectTasks}
            handleOpenParentDialog={handleOpenDialog}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function ProjectsTable({
  projects,
  showProjectTasks,
  setShowProjectTasks,
  handleOpenParentDialog,
}: {
  projects: any[]
  showProjectTasks: string | null
  setShowProjectTasks: (id: string | null) => void
  handleOpenParentDialog: () => void
}) {
  const { getProjectTasks, createProjectTask, updateProject, deleteProject } = useProjects()
  const [tasks, setTasks] = useState<any[]>([])
  const [loadingTasks, setLoadingTasks] = useState(false)
  const [showAddTask, setShowAddTask] = useState(false)
  const [newTask, setNewTask] = useState({
    name: "",
    description: "",
    estimated_hours: 0,
  })

  const fetchTasks = useCallback(
    async (projectId: string) => {
      setLoadingTasks(true)
      try {
        const tasks = await getProjectTasks(projectId)
        setTasks(tasks)
      } catch (err) {
        console.error("Error fetching tasks:", err)
      } finally {
        setLoadingTasks(false)
      }
    },
    [getProjectTasks],
  )

  useEffect(() => {
    if (showProjectTasks) {
      fetchTasks(showProjectTasks)
    }
  }, [showProjectTasks, fetchTasks])

  const handleCreateTask = async () => {
    if (!showProjectTasks) return

    try {
      await createProjectTask(showProjectTasks, newTask)
      setShowAddTask(false)
      setNewTask({
        name: "",
        description: "",
        estimated_hours: 0,
      })
      
      // Add a slight delay before fetching tasks to ensure database has completed the operation
      setTimeout(() => {
        fetchTasks(showProjectTasks)
      }, 500)
    } catch (err) {
      console.error("Error creating task:", err)
    }
  }

  const handleArchiveProject = async (projectId: string) => {
    try {
      await updateProject(projectId, { is_active: false })
    } catch (err) {
      console.error("Error archiving project:", err)
    }
  }

  const handleDeleteProject = async (projectId: string) => {
    try {
      await deleteProject(projectId)
    } catch (err) {
      console.error("Error deleting project:", err)
    }
  }

  // Custom handlers with setTimeout for dialogs
  const handleOpenTaskDialog = () => {
    setTimeout(() => {
      setShowAddTask(true)
    }, 10) // Increase timeout slightly
  }
  
  // This is for the button in the "No projects found" section
  const handleOpenProjectDialog = () => {
    setTimeout(() => {
      // Since this is in a different component, we need to use the parent state setter
      setShowProjectTasks(null) // Make sure we're in the projects view
    }, 0)
  }

  if (projects.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <div className="flex flex-col items-center gap-3">
          <Briefcase className="h-12 w-12 text-gray-500/50" />
          <p>No projects found</p>
          <Button 
            onClick={handleOpenParentDialog}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5 mt-2"
          >
            <Plus className="mr-2 h-4 w-4" />
            Create Project
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div>
      {showProjectTasks ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowProjectTasks(null)}
                className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
              >
                Back to Projects
              </Button>
              <h3 className="text-xl font-semibold text-white">
                {projects.find((p) => p.id === showProjectTasks)?.name} - Tasks
              </h3>
            </div>
            <Button 
              onClick={handleOpenTaskDialog}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5"
            >
              <Plus className="mr-2 h-4 w-4" />
              New Task
            </Button>
            
            <Dialog open={showAddTask} onOpenChange={setShowAddTask}>
              <SimpleDialogContent className="bg-[#0F172A] border-[#1E293B] text-white" style={{ pointerEvents: "auto" }}>
                <DialogHeader>
                  <DialogTitle>Create New Task</DialogTitle>
                  <DialogDescription className="text-gray-400">Add a new task to this project.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="task_name">Task Name</Label>
                    <Input
                      id="task_name"
                      placeholder="Enter task name"
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                      value={newTask.name}
                      onChange={(e) => setNewTask({ ...newTask, name: e.target.value })}
                      autoComplete="off"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="task_description">Description</Label>
                    <Textarea
                      id="task_description"
                      placeholder="Task description"
                      className="bg-[#1E293B] border-[#2D3748] text-white resize-none"
                      value={newTask.description}
                      onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="estimated_hours">Estimated Hours</Label>
                    <Input
                      id="estimated_hours"
                      type="number"
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                      value={newTask.estimated_hours}
                      onChange={(e) => setNewTask({ ...newTask, estimated_hours: Number.parseFloat(e.target.value) })}
                      autoComplete="off"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <DialogClose asChild>
                    <Button
                      variant="outline"
                      className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
                    >
                      Cancel
                    </Button>
                  </DialogClose>
                  <DialogClose asChild>
                    <Button
                      onClick={handleCreateTask}
                      className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                      disabled={!newTask.name}
                    >
                      Create Task
                    </Button>
                  </DialogClose>
                </DialogFooter>
              </SimpleDialogContent>
            </Dialog>
          </div>

          {loadingTasks ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <div className="flex flex-col items-center gap-3">
                <ListTodo className="h-12 w-12 text-gray-500/50" />
                <p>No tasks found for this project</p>
                <Button
                  onClick={handleOpenTaskDialog}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5 mt-2"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Create Task
                </Button>
              </div>
            </div>
          ) : (
            <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
              <CardContent className="p-0">
                <Table>
                  <TableHeader className="bg-[#1E293B]">
                    <TableRow className="hover:bg-[#1E293B]/50 border-[#2D3748]">
                      <TableHead className="text-gray-300 font-medium">Name</TableHead>
                      <TableHead className="text-gray-300 font-medium">Description</TableHead>
                      <TableHead className="text-gray-300 font-medium">Estimated Hours</TableHead>
                      <TableHead className="text-gray-300 font-medium">Status</TableHead>
                      <TableHead className="text-gray-300 font-medium w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tasks.map((task) => (
                      <TableRow key={task.id} className="hover:bg-[#1E293B]/50 border-[#2D3748]">
                        <TableCell className="font-medium text-white">{task.name}</TableCell>
                        <TableCell className="text-gray-300">{task.description || "—"}</TableCell>
                        <TableCell className="text-gray-300">{task.estimated_hours || "—"}</TableCell>
                        <TableCell>
                          {task.is_active ? (
                            <Badge className="bg-green-500/10 text-green-500 hover:bg-green-500/20">Active</Badge>
                          ) : (
                            <Badge className="bg-gray-500/10 text-gray-400 hover:bg-gray-500/20">Inactive</Badge>
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
              </CardContent>
            </Card>
          )}
        </div>
      ) : (
        <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
          <CardContent className="p-0">
            <Table>
              <TableHeader className="bg-[#1E293B]">
                <TableRow className="hover:bg-[#1E293B]/50 border-[#2D3748]">
                  <TableHead className="text-gray-300 font-medium">Name</TableHead>
                  <TableHead className="text-gray-300 font-medium">Client</TableHead>
                  <TableHead className="text-gray-300 font-medium">Hourly Rate</TableHead>
                  <TableHead className="text-gray-300 font-medium">Status</TableHead>
                  <TableHead className="text-gray-300 font-medium">Created</TableHead>
                  <TableHead className="text-gray-300 font-medium w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projects.map((project) => (
                  <TableRow key={project.id} className="hover:bg-[#1E293B]/50 border-[#2D3748]">
                    <TableCell className="font-medium text-white">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: project.color || "#3b82f6" }} />
                        {project.name}
                      </div>
                    </TableCell>
                    <TableCell className="text-gray-300">{project.client_name || "—"}</TableCell>
                    <TableCell className="text-gray-300">
                      {project.hourly_rate ? `$${project.hourly_rate.toFixed(2)}` : "—"}
                    </TableCell>
                    <TableCell>
                      {project.is_active ? (
                        <Badge className="bg-green-500/10 text-green-500 hover:bg-green-500/20">Active</Badge>
                      ) : (
                        <Badge className="bg-gray-500/10 text-gray-400 hover:bg-gray-500/20">Archived</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-gray-300">{formatDate(project.created_at)}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8 p-0 hover:bg-[#2D3748]">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-[#0F172A] border-[#1E293B]">
                          <DropdownMenuItem
                            className="hover:bg-[#1E293B] text-gray-300 hover:text-white"
                            onClick={() => setShowProjectTasks(project.id)}
                          >
                            <ListTodo className="mr-2 h-4 w-4" />
                            <span>View Tasks</span>
                          </DropdownMenuItem>
                          <DropdownMenuItem className="hover:bg-[#1E293B] text-gray-300 hover:text-white">
                            <Edit className="mr-2 h-4 w-4" />
                            <span>Edit</span>
                          </DropdownMenuItem>
                          {project.is_active ? (
                            <DropdownMenuItem
                              className="hover:bg-[#1E293B] text-amber-400 hover:text-amber-300"
                              onClick={() => handleArchiveProject(project.id)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              <span>Archive</span>
                            </DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem
                              className="hover:bg-[#1E293B] text-red-400 hover:text-red-300"
                              onClick={() => handleDeleteProject(project.id)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              <span>Delete</span>
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
