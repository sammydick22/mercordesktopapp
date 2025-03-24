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
  const [lastFetchTime, setLastFetchTime] = useState<number>(0)
  const [fetchInProgress, setFetchInProgress] = useState<boolean>(false)

  const fetchProjects = async (retryCount = 0, force = false) => {
    // If no auth token yet, don't try to fetch
    const token = localStorage.getItem("auth_token");
    if (!token && !force) {
      console.log("No auth token available yet, will retry when available");
      return;
    }
    
    // GLOBAL THROTTLING: Use localStorage to share state between multiple component instances
    const now = Date.now();
    const globalLastFetchTime = parseInt(localStorage.getItem("projects_global_last_fetch") || "0");
    const globalFetchInProgress = localStorage.getItem("projects_fetch_in_progress") === "true";
    const timeSinceLastFetch = now - globalLastFetchTime;
    
    // Use cached data from localStorage if available
    const cachedData = localStorage.getItem("projects_cached_data");
    if (cachedData && !force && projects.length === 0) {
      try {
        const parsed = JSON.parse(cachedData);
        
        // Check if we actually need to update state to avoid re-render loops
        // Only set state if projects is empty and parsed data isn't
        if (projects.length === 0 && parsed.length > 0) {
          console.log("Using projects data from localStorage cache");
          setProjects(parsed);
        } else {
          console.log("Using cached data without state update");
        }
      } catch (e) {
        console.error("Error parsing cached projects data:", e);
      }
    }
    
    // Return immediately if:
    // 1. A fetch is already in progress globally, OR
    // 2. It's been less than 30 seconds since the last fetch AND force is false AND we have data
    if (globalFetchInProgress) {
      console.log("Projects fetch already in progress globally, skipping");
      return;
    }
    
    if (!force && timeSinceLastFetch < 30000 && (projects.length > 0 || cachedData)) {
      console.log(`Using cached projects data (last fetch: ${timeSinceLastFetch/1000}s ago)`);
      return;
    }
    
    // Set global in-progress flag
    localStorage.setItem("projects_fetch_in_progress", "true");
    setFetchInProgress(true);
    setLoading(true);
    setError(null);
    
    try {
      console.log("Fetching projects...");
      const { data } = await projectsApi.getProjects();
      
      // Update global last fetch time
      const fetchTime = Date.now();
      localStorage.setItem("projects_global_last_fetch", fetchTime.toString());
      setLastFetchTime(fetchTime);
      
      if (data && data.projects) {
        console.log(`Fetched ${data.projects.length} projects`);
        setProjects(data.projects);
        
        // Cache data in localStorage
        try {
          localStorage.setItem("projects_cached_data", JSON.stringify(data.projects));
        } catch (e) {
          console.warn("Failed to cache projects in localStorage:", e);
        }
      } else {
        console.warn("Unexpected projects response format:", data);
        setProjects([]);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to fetch projects");
      console.error("Error fetching projects:", err);
      
      // Enhanced retry logic with increasing delays
      if (retryCount < 3) {
        // Calculate delay with exponential backoff (1s, 2s, 4s)
        const delay = Math.min(1000 * Math.pow(2, retryCount), 4000);
        console.log(`Retrying projects fetch (${retryCount + 1}/3) in ${delay}ms...`);
        setTimeout(() => fetchProjects(retryCount + 1, force), delay);
        return;
      }
    } finally {
      setLoading(false);
      setFetchInProgress(false);
      localStorage.setItem("projects_fetch_in_progress", "false");
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

  // Clear in-progress flag on unmount to prevent deadlocks
  useEffect(() => {
    return () => {
      localStorage.setItem("projects_fetch_in_progress", "false");
    };
  }, []);

  // Initial fetch effect - only runs once on mount
  useEffect(() => {
    fetchProjects()
  }, [])
  
  // Add effect to handle localStorage events and sync between components
  useEffect(() => {
    // Listen for auth token changes
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === "auth_token" && event.newValue) {
        console.log("Auth token changed, fetching projects");
        fetchProjects(0, true); // Force refresh with retryCount=0
      }
    };
    
    // Listen for global fetch completed events
    const handleFetchComplete = (event: StorageEvent) => {
      if (event.key === "projects_global_last_fetch" && event.newValue) {
        // Another instance has completed a fetch, we should check our local state
        const cachedData = localStorage.getItem("projects_cached_data");
        if (cachedData && projects.length === 0) {
          try {
            const parsedData = JSON.parse(cachedData);
            // Only update state if there's actual data and our current state is empty
            if (parsedData && parsedData.length > 0 && projects.length === 0) {
              console.log("Another instance fetched data, updating local state");
              setProjects(parsedData);
            }
          } catch (e) {
            console.error("Error parsing cached projects data:", e);
          }
        }
      }
    };
    
    // Listen for storage events
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('storage', handleFetchComplete);
    
    // Check for cached data on mount if we have no projects
    if (projects.length === 0) {
      const cachedData = localStorage.getItem("projects_cached_data");
      if (cachedData) {
        try {
          console.log("Loading projects from cache on mount");
          setProjects(JSON.parse(cachedData));
        } catch (e) {
          console.error("Error parsing cached projects data:", e);
        }
      }
    }
    
    // Return cleanup function
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('storage', handleFetchComplete);
    };
  }, []);

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
