import apiClient from './client'

// Time window endpoints
export const getInsightfulTimeWindows = (params: {
  start: number;
  end: number;
  timezone?: string;
  employeeId?: string;
  teamId?: string;
  projectId?: string;
  taskId?: string;
  shiftId?: string;
}) => {
  return apiClient.get('/insightful/time-windows', { params });
}

// Project time endpoints
export const getInsightfulProjectTime = (params: {
  start: number;
  end: number;
  timezone?: string;
  employeeId?: string;
  teamId?: string;
  projectId?: string;
  taskId?: string;
  shiftId?: string;
}) => {
  return apiClient.get('/insightful/project-time', { params });
}

// Screenshot endpoints
export const getInsightfulScreenshots = (params: {
  start: number;
  end: number;
  timezone?: string;
  taskId?: string;
  projectId?: string;
  limit?: number;
  next_token?: string;
}) => {
  return apiClient.get('/insightful/screenshots', { params });
}

// Employee endpoint
export const deactivateInsightfulEmployee = (employeeId: string) => {
  return apiClient.get(`/insightful/employee/deactivate/${employeeId}`);
}

// Task endpoint
export const deleteInsightfulTask = (taskId: string) => {
  return apiClient.delete(`/insightful/task/${taskId}`);
}

// Project endpoint
export const deleteInsightfulProject = (projectId: string) => {
  return apiClient.delete(`/insightful/project/${projectId}`);
}

// Utility functions for working with timestamps
export const dateToTimestamp = (date: Date): number => {
  return date.getTime();
}

export const timestampToDate = (timestamp: number): Date => {
  return new Date(timestamp);
}

// Get start and end timestamps for common time periods
export const getTimeRangeForPeriod = (period: 'today' | 'yesterday' | 'week' | 'month'): { start: number, end: number } => {
  const now = new Date();
  let start: Date;
  let end: Date = now;
  
  switch (period) {
    case 'today':
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      break;
    case 'yesterday':
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
      end = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      break;
    case 'week':
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 7);
      break;
    case 'month':
      start = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
      break;
    default:
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  }
  
  return {
    start: start.getTime(),
    end: end.getTime()
  };
}
