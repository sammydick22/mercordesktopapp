# Time Tracker Desktop App Backend

This is the Python backend for the Time Tracker desktop application with Supabase integration.

## Setup

1. Ensure you have Python 3.8+ installed
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure your `.env` file is properly configured with Supabase credentials:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

## Testing Supabase Integration

You can test the Supabase authentication integration using the provided test script:

```bash
python test_supabase_auth.py
```

This will prompt you for test credentials and verify that authentication, token validation, and session management are working correctly.

## Running the API

To start the FastAPI server:

```bash
cd desktop_app/python
uvicorn api.main:app --reload
```

The API will be available at http://localhost:8000

You can access the API documentation at http://localhost:8000/docs

## API Endpoints

The API provides the following endpoint groups:

### Authentication
- **POST /auth/login** - User login
- **POST /auth/signup** - User registration
- **POST /auth/logout** - User logout
- **POST /auth/refresh** - Refresh authentication token
- **GET /auth/user** - Get current user
- **POST /auth/reset-password** - Send password reset email

### Time Entries
- **POST /time-entries/start** - Start a time entry
- **POST /time-entries/stop** - Stop the active time entry
- **GET /time-entries/current** - Get the current time entry
- **GET /time-entries/** - List time entries

### Screenshots
- **POST /screenshots/capture** - Capture a screenshot
- **GET /screenshots/** - List screenshots
- **GET /screenshots/{id}** - Get screenshot metadata
- **GET /screenshots/{id}/image** - Get screenshot image
- **GET /screenshots/{id}/thumbnail** - Get screenshot thumbnail

### Synchronization
- **POST /sync/all** - Sync all data
- **POST /sync/activities** - Sync only activities
- **POST /sync/screenshots** - Sync only screenshots
- **POST /sync/organization** - Sync organization data
- **GET /sync/status** - Get sync status
- **POST /sync/background** - Start background sync

## Authentication

All endpoints (except /auth/login, /auth/signup, and /auth/reset-password) require authentication using a Bearer token in the Authorization header:

```
Authorization: Bearer your-access-token
```

The access token is obtained from the /auth/login endpoint.
