# Insightful-Compatible API Integration Guide

This guide explains how to use the Insightful-compatible API endpoints with the Time Tracker desktop application.

## Overview

The Time Tracker app now includes endpoints that mimic Insightful's API structure but use your local database, allowing you to:

- Delete projects and tasks using Insightful's API format
- Deactivate employees using Insightful's API format
- Retrieve screenshots formatted like Insightful's API
- Retrieve time tracking data formatted like Insightful's API
- Analyze project time usage formatted like Insightful's API

This implementation allows your application to be compatible with systems designed for Insightful, without requiring an actual Insightful account or API token.

## Setup

No special setup is required. The endpoints work with your existing database and authentication system.

For testing purposes, you can add your authentication token to the `.env` file:

```
AUTH_TOKEN=your-authentication-token-here
```

## Backend API Endpoints

The following Insightful-compatible endpoints are available:

### Employee Management

- `GET /insightful/employee/deactivate/{employee_id}` - Deactivate an employee

### Project Management

- `DELETE /insightful/project/{project_id}` - Delete a project in Insightful

### Task Management

- `DELETE /insightful/task/{task_id}` - Delete a task in Insightful

### Screenshots

- `GET /insightful/screenshots` - Get screenshots from Insightful
  - Required parameters:
    - `start` (millisecond timestamp)
    - `end` (millisecond timestamp)
  - Optional parameters:
    - `timezone`
    - `taskId`
    - `projectId`
    - `limit`
    - `next_token`

### Time Tracking

- `GET /insightful/time-windows` - Get time tracking windows
  - Required parameters:
    - `start` (millisecond timestamp)
    - `end` (millisecond timestamp)
  - Optional parameters:
    - `timezone`
    - `employeeId`
    - `teamId`
    - `projectId`
    - `taskId`
    - `shiftId`

- `GET /insightful/project-time` - Get project time analytics
  - Required parameters:
    - `start` (millisecond timestamp)
    - `end` (millisecond timestamp) 
  - Optional parameters:
    - `timezone`
    - `employeeId`
    - `teamId`
    - `projectId`
    - `taskId`
    - `shiftId`

## Frontend Integration

### Using the Insightful API Client

Import the Insightful API client functions in your frontend components:

```typescript
import { 
  getInsightfulTimeWindows,
  getInsightfulProjectTime,
  getInsightfulScreenshots,
  deactivateInsightfulEmployee,
  deleteInsightfulTask,
  deleteInsightfulProject,
  getTimeRangeForPeriod
} from '../api/insightful';
```

### Example Usage

```typescript
// Get time windows for today
const timeRange = getTimeRangeForPeriod('today');
const response = await getInsightfulTimeWindows({
  start: timeRange.start,
  end: timeRange.end,
  employeeId: 'employee-id'
});

// Delete a task
await deleteInsightfulTask('task-id');

// Deactivate an employee
await deactivateInsightfulEmployee('employee-id');
```

## Testing the Integration

A test script is provided to verify the Insightful-compatible API endpoints:

```bash
cd python
python test_insightful_api.py
```

This script demonstrates how to retrieve screenshots, time windows, and project time using the Insightful-compatible format.

## Troubleshooting

1. **Authorization Errors**
   
   If you encounter 401 Unauthorized errors, verify that:
   - You're using a valid authentication token for the Time Tracker API
   - The token has not expired
   - The token belongs to a user with appropriate permissions

2. **Request Errors**
   
   For errors in API requests:
   - Check the required parameters are provided (especially `start` and `end` timestamps)
   - Ensure timestamps are in milliseconds (multiply by 1000 if using seconds)
   - Verify that IDs (employee, project, task) exist in your database

3. **Integration Issues**
   
   If the integration is not working as expected:
   - Check the server logs for detailed error messages
   - Verify that your database schema matches what the endpoints expect
   - Test the API endpoints directly using tools like Postman or curl
   - Ensure your database has appropriate test data for screenshots, time entries, etc.
   
4. **Schema Differences**

   If you encounter errors related to database queries:
   - The implementation assumes certain table and column names
   - You may need to adjust the SQL queries in `insightful.py` to match your actual database schema
