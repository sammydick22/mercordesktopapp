# Supabase Sync Guide for TimeTracker

This guide explains how to set up and test the synchronization between your local TimeTracker app and Supabase.

## Prerequisites

1. A Supabase project (create one at [supabase.com](https://supabase.com) if you don't have one)
2. Python 3.9 or higher
3. All required Python dependencies installed (see `requirements.txt`)

## Setup Steps

### 1. Configure Environment Variables

Create or update your `.env` file in the `desktop_app/python/` directory with your Supabase credentials:

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

You can find these values in your Supabase project dashboard under Settings > API.

### 2. Set Up Supabase Schema

The file `supabase_schema.sql` contains all the SQL statements needed to create the required tables and security policies in your Supabase project.

To apply this schema:

1. Log in to your Supabase dashboard
2. Go to the SQL Editor
3. Create a new query
4. Paste the contents of `supabase_schema.sql`
5. Run the query

> **Note**: Ignore any SQL syntax errors shown in VS Code for this file. The schema is written for PostgreSQL with Supabase extensions, which VS Code's SQL validator may not fully understand.

### 3. Create a Test User

For testing purposes, you need a user account in your Supabase project:

1. In your Supabase dashboard, go to Authentication > Users
2. Click "Add User"
3. Enter an email and password
4. Note the user's UUID (you'll need it for the next step)

### 4. Add User to Test Organization

After running the schema setup, you need to add your test user to the "Test Organization":

1. In the SQL Editor, run the following query (replace `YOUR-USER-ID` with the actual UUID):

```sql
INSERT INTO org_members (org_id, user_id, role)
VALUES 
  ((SELECT id FROM organizations WHERE name = 'Test Organization'), 'YOUR-USER-ID', 'admin');
```

### 5. Create a Storage Bucket

The sync service requires a storage bucket named "screenshots":

1. Go to Storage in your Supabase dashboard
2. Click "Create a new bucket"
3. Name it "screenshots"
4. Enable public access (for testing purposes)

## Testing Sync Functionality

### Authentication Test

First, test that authentication works:

```bash
cd desktop_app/python
python test_supabase_auth.py
```

When prompted, enter the email and password for your test user.

### Activity Testing

Generate some activity data to sync:

```bash
python test_activity_tracking.py
```

### Sync Testing

Finally, test the sync functionality:

```bash
python test_supabase_sync.py
```

This script will:
1. Authenticate with your Supabase project
2. Generate test data if needed
3. Sync organization data from Supabase to local database
4. Sync activity logs from local database to Supabase
5. Sync screenshots from local storage to Supabase Storage

## Troubleshooting

### Missing Python Dependencies

If you encounter import errors, install the required dependencies:

```bash
pip install python-dotenv supabase pyjwt
```

### Authentication Issues

- Verify your SUPABASE_URL and SUPABASE_ANON_KEY are correct
- Ensure the email and password you're using match a user in your Supabase project

### Sync Issues

- Check that the tables exist in your Supabase project
- Verify that your user is a member of an organization
- Ensure the "screenshots" storage bucket exists and is accessible
