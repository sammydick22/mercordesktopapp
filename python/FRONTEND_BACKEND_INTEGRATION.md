# TimeTracker Frontend-Backend Integration Guide

This document provides comprehensive guidance for implementing the Next.js frontend for the TimeTracker application and integrating it with the Python FastAPI backend.

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Authentication Flow](#authentication-flow)
4. [API Endpoints](#api-endpoints)
5. [Data Models](#data-models)
6. [Frontend Implementation](#frontend-implementation)
7. [Local Development Setup](#local-development-setup)
8. [Production Considerations](#production-considerations)

## Overview

TimeTracker is a comprehensive time tracking application that allows users to:

- Track time spent on different tasks and projects
- Capture screenshots automatically during tracking sessions
- Sync data with Supabase for cloud storage and multi-device access
- View activity reports and analytics
- Manage project and client information

The system consists of:
- A FastAPI Python backend that manages local data and interacts with Supabase
- A Next.js frontend that provides the user interface
- An Electron wrapper (to be added later) that will convert the web app into a desktop application

## System Architecture

```
┌────────────────────────────────────┐
│           Electron App             │
│  ┌────────────────────────────┐    │
│  │       Next.js Frontend     │    │
│  └─────────────┬──────────────┘    │
│                │                   │
│  ┌─────────────▼──────────────┐    │
│  │      FastAPI Backend       │    │
│  └─────────────┬──────────────┘    │
└────────────────┼────────────────────┘
                 │
       ┌─────────▼─────────┐
       │     Supabase      │
       └───────────────────┘
```

### Communication Flow:

1. The Next.js frontend communicates with the FastAPI backend via HTTP requests to the local server
2. The FastAPI backend stores data locally in SQLite and syncs with Supabase
3. Authentication is handled through Supabase, with session tokens managed by the backend
4. The Electron wrapper (future addition) will provide native OS integration

## Authentication Flow

The application uses Supabase for authentication. The frontend should implement this flow:

1. **Login/Signup Process**:
   - User enters credentials in the Next.js frontend
   - Frontend sends credentials to the local backend API
   - Backend authenticates with Supabase and returns session information
   - Frontend stores the session token for subsequent requests

2. **Session Management**:
   - Frontend should check session validity on app start
   - Provide a mechanism to refresh tokens when needed
   - Handle logout by clearing local session and calling the logout endpoint

3. **Authorization**:
   - All API endpoints (except health checks and auth endpoints) require authentication
   - The frontend should include the auth token in all requests

## API Endpoints

The FastAPI backend exposes the following endpoints:

### Base URL: `http://localhost:8000`

### Authentication Endpoints

```
POST /auth/login             - Sign in with email/password
POST /auth/signup            - Register a new user
POST /auth/logout            - Sign out current user
POST /auth/refresh           - Refresh authentication token
GET  /auth/user              - Get current user information
POST /auth/reset-password    - Request password reset email
```

### Time Entry Endpoints

```
POST /time-entries/start     - Start a new time entry
POST /time-entries/stop      - Stop the current time entry
GET  /time-entries/current   - Get the current active time entry
GET  /time-entries           - List time entries with pagination
```

### Screenshot Endpoints

```
POST /screenshots/capture    - Capture a screenshot
GET  /screenshots            - List screenshots with pagination
GET  /screenshots/{id}       - Get screenshot metadata
GET  /screenshots/{id}/image - Get the screenshot image
GET  /screenshots/{id}/thumbnail - Get the screenshot thumbnail
```

### Synchronization Endpoints

```
POST /sync/all               - Sync all data with Supabase
POST /sync/activities        - Sync only activity logs
POST /sync/screenshots       - Sync only screenshots
POST /sync/organization      - Sync only organization data
GET  /sync/status            - Get current sync status
POST /sync/background        - Start background sync process
```

### Health Check

```
GET  /health                 - Check if API is operational
```

## Data Models

### User

```typescript
interface User {
  id: string;
  email: string;
  created_at: string;
  last_sign_in_at?: string;
}
```

### Time Entry

```typescript
interface TimeEntry {
  id: string;
  start_time: string;  // ISO datetime
  end_time?: string;   // ISO datetime
  duration?: number;   // seconds
  project_id?: string;
  task_id?: string;
  description?: string;
  is_active: boolean;
  synced: boolean;
}
```

### Screenshot

```typescript
interface Screenshot {
  id: string;
  timestamp: string;     // ISO datetime
  filepath: string;      // Local file path
  thumbnail_path: string;
  time_entry_id?: string;
  synced: boolean;
}
```

### Sync Status

```typescript
interface SyncStatus {
  initialized: boolean;
  is_syncing: boolean;
  sync_error?: string;
  last_sync: {
    activity_logs?: {
      last_id: number;
      last_time: string;
    };
    screenshots?: {
      last_id: number;
      last_time: string;
    };
  };
}
```

## Frontend Implementation

### Required Pages

1. **Authentication Pages**:
   - Login page
   - Signup page
   - Password reset request page
   - Password reset completion page

2. **Dashboard**:
   - Overview of recent time entries
   - Current tracking status
   - Quick stats and summaries
   - Sync status indicator

3. **Time Tracking**:
   - Timer controls (start/stop)
   - Project/task selection
   - Description input
   - Current/recent screenshots

4. **Time Entries**:
   - List view with filtering options
   - Edit/delete capabilities
   - Sorting and grouping
   - Export functionality

5. **Screenshots**:
   - Gallery view with time information
   - Filtering by time entry/date
   - Lightbox for viewing full images

6. **Settings**:
   - User profile management
   - Screenshot capturing preferences
   - Synchronization settings
   - Application preferences

### State Management

Use React Context or a state management library like Redux to handle:

1. **Authentication State**:
   - Current user information
   - Login status
   - Session tokens

2. **Time Tracking State**:
   - Current time entry
   - Active timer status
   - Recent entries

3. **Sync State**:
   - Sync status
   - Last sync timestamps
   - Pending changes

### Real-time Updates

For time tracking to feel responsive:

1. Implement a polling mechanism to check the status of the current time entry
2. Update timer displays in real-time on the client side
3. Refresh data after sync operations complete

### API Communication

Create a centralized API client:

```typescript
// api/client.ts
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        // Call refresh token endpoint
        const { data } = await apiClient.post('/auth/refresh');
        // Update stored token
        localStorage.setItem('auth_token', data.session.access_token);
        // Retry the original request
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Handle refresh failure (logout, etc.)
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Authentication Implementation

```typescript
// api/auth.ts
import apiClient from './client';

export const login = (email: string, password: string) => 
  apiClient.post('/auth/login', { email, password });

export const signup = (email: string, password: string) => 
  apiClient.post('/auth/signup', { email, password });

export const logout = () => 
  apiClient.post('/auth/logout');

export const getCurrentUser = () => 
  apiClient.get('/auth/user');

export const resetPassword = (email: string) => 
  apiClient.post('/auth/reset-password', { email });
```

### Time Tracking Implementation

```typescript
// api/timeEntries.ts
import apiClient from './client';

export const startTimeEntry = (projectId?: string, taskId?: string, description?: string) => 
  apiClient.post('/time-entries/start', { project_id: projectId, task_id: taskId, description });

export const stopTimeEntry = (description?: string) => 
  apiClient.post('/time-entries/stop', { description });

export const getCurrentTimeEntry = () => 
  apiClient.get('/time-entries/current');

export const getTimeEntries = (limit = 10, offset = 0) => 
  apiClient.get('/time-entries', { params: { limit, offset } });
```

### Screenshots Implementation

```typescript
// api/screenshots.ts
import apiClient from './client';

export const captureScreenshot = (timeEntryId?: string) => 
  apiClient.post('/screenshots/capture', { time_entry_id: timeEntryId });

export const getScreenshots = (limit = 10, offset = 0, timeEntryId?: string) => 
  apiClient.get('/screenshots', { params: { limit, offset, time_entry_id: timeEntryId } });

export const getScreenshotUrl = (screenshotId: string) => 
  `${apiClient.defaults.baseURL}/screenshots/${screenshotId}/image`;

export const getScreenshotThumbnailUrl = (screenshotId: string) => 
  `${apiClient.defaults.baseURL}/screenshots/${screenshotId}/thumbnail`;
```

### Sync Implementation

```typescript
// api/sync.ts
import apiClient from './client';

export const syncAll = () => 
  apiClient.post('/sync/all');

export const syncActivities = () => 
  apiClient.post('/sync/activities');

export const syncScreenshots = () => 
  apiClient.post('/sync/screenshots');

export const syncOrganization = () => 
  apiClient.post('/sync/organization');

export const getSyncStatus = () => 
  apiClient.get('/sync/status');

export const startBackgroundSync = () => 
  apiClient.post('/sync/background');
```

## UI Components

Recommended UI components to implement:

1. **Timer Control**:
   - Display of current time
   - Start/stop buttons
   - Project/task selection
   - Description input

2. **Time Entry Card**:
   - Display entry duration
   - Show start/end times
   - Project/task information
   - Edit/delete buttons

3. **Screenshot Thumbnail**:
   - Image preview
   - Timestamp
   - Associated time entry
   - Lightbox integration

4. **Sync Status Indicator**:
   - Current sync state
   - Last sync time
   - Manual sync button
   - Error indication

5. **Project/Task Selector**:
   - Hierarchical display
   - Search functionality
   - Recent/favorite selections
   - Create new option

## Local Development Setup

1. **Environment Setup**:
   - Create a `.env.local` file in the Next.js root:
     ```
     NEXT_PUBLIC_API_URL=http://localhost:8000
     ```

2. **CORS Configuration**:
   - The backend already has CORS configured to allow requests from `http://localhost:3000`
   - No additional configuration is needed for local development

3. **Development Workflow**:
   - Start the Python backend:
     ```
     cd desktop_app/python
     uvicorn api.main:app --reload
     ```
   - Start the Next.js development server:
     ```
     cd web_app
     npm run dev
     ```

## Production Considerations

1. **API Communication**:
   - The frontend will communicate with the backend on the same machine in the Electron app
   - Use IPC for more efficient communication in the Electron wrapper (future implementation)

2. **Authentication**:
   - Token storage should use secure storage mechanisms in production
   - Consider session persistence across app restarts

3. **Offline Support**:
   - Implement queuing for operations when offline
   - Show sync status clearly to users
   - Provide retry mechanisms for failed operations

4. **Error Handling**:
   - Implement comprehensive error handling for all API calls
   - Provide user-friendly error messages
   - Log errors for debugging purposes

5. **Performance**:
   - Optimize image loading for screenshot galleries
   - Implement virtualization for long lists
   - Consider lazy loading for less frequently used features

## Conclusion

This document provides the architectural overview and integration details needed to implement the Next.js frontend for the TimeTracker application. The frontend should provide a seamless user experience while effectively communicating with the Python backend and displaying data from the local database and Supabase.

For more detailed information about specific API endpoints or data models, refer to the Python backend code or contact the backend team.
