"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import * as projectsApi from "@/api/projects"

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

interface Project {
  id: string
  name: string
  client_id?: string
  client_name?: string
  description?: string
  color?: string
  hourly_rate?: number
  is_billable: boolean
  is_active: boolean
  created_at: string
  updated_at: string
  tasks?: Task[]
}

interface ProjectsContextType {
  projects: Project[]
  activeProjects: Project[]
  loading: boolean
  error: string | null
  fetchProjects: () => Promise<void>
  getProject: (id: string) => Promise<Project>
  createProject: (data: {
    name: string
    client_id?: string
    description?: string
    color?: string
    hourly_rate?: number
    is_billable?: boolean
  }) => Promise<Project>
  updateProject: (
    id: string,
    data: {
      name?: string
      client_id?: string
      description?: string
      color?: string
      hourly_rate?: number
      is_billable?: boolean
      is_active?: boolean
    },
  ) => Promise<Project>
  deleteProject: (id: string) => Promise<void>
  getProjectTasks: (projectId: string) => Promise<Task[]>
  createProjectTask: (
    projectId: string,
    data: {
      name: string
      description?: string
      estimated_hours?: number
    },
  ) => Promise<Task>
  updateProjectTask: (
    projectId: string,
    taskId: string,
    data: {
      name?: string
      description?: string
      estimated_hours?: number
      is_active?: boolean
    },
  ) => Promise<Task>
  deleteProjectTask: (projectId: string, taskId: string) => Promise<void>
}

const ProjectsContext = createContext<ProjectsContextType | undefined>(undefined)

export function ProjectsProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchProjects = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await projectsApi.getProjects()
      setProjects(data.projects || [])
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to fetch projects")
      console.error("Error fetching projects:", err)
    } finally {
      setLoading(false)
    }
  }

  const getProject = async (id: string): Promise<Project> => {
    try {
      const { data } = await projectsApi.getProject(id)
      return data.project
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to fetch project")
    }
  }

  const createProject = async (projectData: {
    name: string
    client_id?: string
    description?: string
    color?: string
    hourly_rate?: number
    is_billable?: boolean
  }): Promise<Project> => {
    try {
      const { data } = await projectsApi.createProject(projectData)
      setProjects((prev) => [...prev, data.project])
      return data.project
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to create project")
    }
  }

  const updateProject = async (
    id: string,
    projectData: {
      name?: string
      client_id?: string
      description?: string
      color?: string
      hourly_rate?: number
      is_billable?: boolean
      is_active?: boolean
    },
  ): Promise<Project> => {
    try {
      const { data } = await projectsApi.updateProject(id, projectData)
      setProjects((prev) => prev.map((project) => (project.id === id ? data.project : project)))
      return data.project
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to update project")
    }
  }

  const deleteProject = async (id: string): Promise<void> => {
    try {
      await projectsApi.deleteProject(id)
      setProjects((prev) => prev.filter((project) => project.id !== id))
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to delete project")
    }
  }

  const getProjectTasks = async (projectId: string): Promise<Task[]> => {
    try {
      const { data } = await projectsApi.getProjectTasks(projectId)
      return data.tasks || []
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to fetch project tasks")
    }
  }

  const createProjectTask = async (
    projectId: string,
    taskData: {
      name: string
      description?: string
      estimated_hours?: number
    },
  ): Promise<Task> => {
    try {
      const { data } = await projectsApi.createProjectTask(projectId, taskData)
      return data.task
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to create task")
    }
  }

  const updateProjectTask = async (
    projectId: string,
    taskId: string,
    taskData: {
      name?: string
      description?: string
      estimated_hours?: number
      is_active?: boolean
    },
  ): Promise<Task> => {
    try {
      const { data } = await projectsApi.updateProjectTask(projectId, taskId, taskData)
      return data.task
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to update task")
    }
  }

  const deleteProjectTask = async (projectId: string, taskId: string): Promise<void> => {
    try {
      await projectsApi.deleteProjectTask(projectId, taskId)
    } catch (err: any) {
      throw new Error(err.response?.data?.message || "Failed to delete task")
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  const activeProjects = projects.filter((project) => project.is_active)

  return (
    <ProjectsContext.Provider
      value={{
        projects,
        activeProjects,
        loading,
        error,
        fetchProjects,
        getProject,
        createProject,
        updateProject,
        deleteProject,
        getProjectTasks,
        createProjectTask,
        updateProjectTask,
        deleteProjectTask,
      }}
    >
      {children}
    </ProjectsContext.Provider>
  )
}

export function useProjects() {
  const context = useContext(ProjectsContext)
  if (context === undefined) {
    throw new Error("useProjects must be used within a ProjectsProvider")
  }
  return context
}

