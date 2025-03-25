# Schema Comparison: Supabase vs Local SQLite

This document compares the schema structures between the Supabase PostgreSQL database and the local SQLite database to ensure synchronization compatibility.

## Table Comparison

### Tables Present in Both Databases
- activity_logs
- screenshots
- clients
- projects
- project_tasks
- user_settings
- user_profiles

### Supabase-Specific Tables
- organizations
- org_members

### Local SQLite-Specific Tables
- system_metrics
- sync_status
- user_config

## Detailed Field Comparison by Table

### activity_logs

| Field | Supabase | SQLite | Compatibility Notes |
|-------|----------|--------|---------------------|
| id | uuid PRIMARY KEY | INTEGER PRIMARY KEY AUTOINCREMENT | Different PK types. Sync needs to map between them |
| user_id | uuid REFERENCES auth.users(id) | *Missing* | Required in Supabase for RLS; needs to be populated during sync |
| org_id | uuid REFERENCES organizations(id) | *Missing* | Required in Supabase for RLS; needs to be populated during sync |
| window_title | text NOT NULL | TEXT NOT NULL | Compatible |
| process_name | text NOT NULL | TEXT NOT NULL | Compatible |
| executable_path | text | TEXT | Compatible |
| start_time | timestamp with time zone NOT NULL | TIMESTAMP NOT NULL | Type conversion needed |
| end_time | timestamp with time zone | TIMESTAMP | Type conversion needed |
| duration | integer | INTEGER | Compatible |
| client_created_at | timestamp with time zone | *Missing* | Used for offline sync timing; should be added to SQLite or populated during sync |
| created_at | timestamp with time zone NOT NULL DEFAULT NOW() | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Compatible with conversion |
| updated_at | timestamp with time zone NOT NULL DEFAULT NOW() | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Compatible with conversion |
| is_active | *Missing* | BOOLEAN NOT NULL DEFAULT 1 | SQLite-specific for activity tracking |
| synced | *Missing* | BOOLEAN NOT NULL DEFAULT 0 | SQLite-specific for sync tracking |

### screenshots

| Field | Supabase | SQLite | Compatibility Notes |
|-------|----------|--------|---------------------|
| id | uuid PRIMARY KEY | INTEGER PRIMARY KEY AUTOINCREMENT | Different PK types. Sync needs to map between them |
| user_id | uuid REFERENCES auth.users(id) | *Missing* | Required in Supabase for RLS; needs to be populated during sync |
| org_id | uuid REFERENCES organizations(id) | *Missing* | Required in Supabase for RLS; needs to be populated during sync |
| activity_log_id | uuid REFERENCES activity_logs(id) | INTEGER REFERENCES activity_logs(id) | Type conversion needed |
| image_url | text NOT NULL | *Missing* (uses filepath) | Data mapping needed during sync |
| thumbnail_url | text | *Missing* (uses thumbnail_path) | Data mapping needed during sync |
| filepath | *Missing* | TEXT NOT NULL | SQLite-specific field; mapped to image_url in Supabase |
| thumbnail_path | *Missing* | TEXT | SQLite-specific field; mapped to thumbnail_url in Supabase |
| taken_at | timestamp with time zone NOT NULL | *Missing* (uses timestamp) | Field name difference |
| timestamp | *Missing* | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Maps to taken_at |
| client_created_at | timestamp with time zone | *Missing* | Used for offline sync timing |
| created_at | timestamp with time zone NOT NULL DEFAULT NOW() | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Compatible with conversion |
| synced | *Missing* | BOOLEAN NOT NULL DEFAULT 0 | SQLite-specific for sync tracking |

### clients

| Field | Supabase | SQLite | Compatibility Notes |
|-------|----------|--------|---------------------|
| id | uuid PRIMARY KEY | TEXT PRIMARY KEY | SQLite uses TEXT for UUID compatibility |
| user_id | uuid NOT NULL REFERENCES auth.users(id) | TEXT | Type compatibility needs to be ensured |
| org_id | uuid NOT NULL REFERENCES organizations(id) | *Missing* | Required in Supabase for RLS; needs to be populated during sync |
| name | text NOT NULL | TEXT NOT NULL | Compatible |
| contact_name | text | TEXT | Compatible |
| email | text | TEXT | Compatible |
| phone | text | TEXT | Compatible |
| address | text | TEXT | Compatible |
| notes | text | TEXT | Compatible |
| is_active | boolean DEFAULT TRUE | INTEGER NOT NULL DEFAULT 1 | Boolean vs INTEGER type conversion |
| client_created_at | timestamp with time zone DEFAULT NOW() | *Missing* | Used for offline sync timing |
| created_at | timestamp with time zone NOT NULL DEFAULT NOW() | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Compatible with conversion |
| updated_at | timestamp with time zone NOT NULL DEFAULT NOW() | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Compatible with conversion |
| synced | *Missing* | INTEGER NOT NULL DEFAULT 0 | SQLite-specific for sync tracking |

### projects

| Field | Supabase | SQLite | Compatibility Notes |
|-------|----------|--------|---------------------|
| id | uuid PRIMARY KEY | TEXT PRIMARY KEY | SQLite uses TEXT for UUID compatibility |
| user_id | uuid NOT NULL REFERENCES auth.users(id) | TEXT | Type compatibility needs to be ensured |
| org_id | uuid NOT NULL REFERENCES organizations(id) | *Missing* | Required in Supabase for RLS; needs to be populated during sync |
| client_id | uuid REFERENCES clients(id) | TEXT REFERENCES clients(id) | Type conversion but both use same reference concept |
| name | text NOT NULL | TEXT NOT NULL | Compatible |
| description | text | TEXT | Compatible |
| color | text | TEXT | Compatible |
| hourly_rate | numeric | REAL | Type conversion needed |
| is_billable | boolean DEFAULT TRUE | INTEGER NOT NULL DEFAULT 1 | Boolean vs INTEGER type conversion |
| is_active | boolean NOT NULL DEFAULT TRUE | INTEGER NOT NULL DEFAULT 1 | Boolean vs INTEGER type conversion |
| client_created_at | timestamp with time zone DEFAULT NOW() | *Missing* | Used for offline sync timing |
| created_at | timestamp with time zone NOT NULL DEFAULT NOW() | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Compatible with conversion |
| updated_at | timestamp with time zone NOT NULL DEFAULT NOW() | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Compatible with conversion |
| synced | *Missing* | INTEGER NOT NULL DEFAULT 0 | SQLite-specific for sync tracking |

### user_settings

| Field | Supabase | SQLite | Compatibility Notes |
|-------|----------|--------|---------------------|
| user_id | uuid PRIMARY KEY | TEXT PRIMARY KEY | Type conversion needed |
| screenshot_interval | integer DEFAULT 600 | INTEGER DEFAULT 600 | Compatible |
| screenshot_quality | text DEFAULT 'medium' | TEXT DEFAULT 'medium' | Compatible |
| auto_sync_interval | integer DEFAULT 300 | INTEGER DEFAULT 300 | Compatible |
| idle_detection_timeout | integer DEFAULT 300 | INTEGER DEFAULT 300 | Compatible |
| theme | text DEFAULT 'system' | TEXT DEFAULT 'system' | Compatible |
| notifications_enabled | boolean DEFAULT TRUE | INTEGER DEFAULT 1 | Boolean vs INTEGER type conversion |
| client_created_at | *Missing* | TIMESTAMP DEFAULT NOW() | Used for offline sync timing |
| created_at | timestamp with time zone NOT NULL DEFAULT NOW() | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Compatible with conversion |
| updated_at | timestamp with time zone NOT NULL DEFAULT NOW() | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Compatible with conversion |
| synced | *Missing* | INTEGER NOT NULL DEFAULT 0 | SQLite-specific for sync tracking |

### user_profiles

| Field | Supabase | SQLite | Compatibility Notes |
|-------|----------|--------|---------------------|
| id/user_id | uuid PRIMARY KEY | TEXT PRIMARY KEY | Different field name but same concept |
| full_name/name | text | TEXT | Different field name but same concept |
| avatar_url | text | TEXT | Compatible |
| role | text | *Missing* | Supabase-specific field |
| timezone | text | TEXT DEFAULT 'UTC' | Compatible |
| email | *Missing* | TEXT | SQLite-specific field |
| hourly_rate | *Missing* | REAL DEFAULT 0 | SQLite-specific field |
| created_at | timestamp with time zone DEFAULT NOW() | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Compatible with conversion |
| updated_at | timestamp with time zone DEFAULT NOW() | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | Compatible with conversion |
| synced | *Missing* | INTEGER NOT NULL DEFAULT 0 | SQLite-specific for sync tracking |

## Synchronization Compatibility Issues

The following are key issues that need to be addressed for proper synchronization:

1. **Primary Key Types**: 
   - Supabase uses UUID for most primary keys
   - SQLite uses INTEGER for sequence-based tables and TEXT for UUID-compatible tables
   - Sync logic must handle this conversion

2. **Data Type Conversions**:
   - Boolean values in Supabase vs INTEGER (0/1) in SQLite
   - Timestamp formats differ between PostgreSQL and SQLite
   - Numeric/decimal precision in PostgreSQL vs REAL in SQLite

3. **Multi-tenant Columns**:
   - Supabase requires user_id and org_id in most tables for Row Level Security (RLS)
   - These must be populated during sync operations

4. **Sync Status Tracking**:
   - SQLite has sync-related columns like "synced" and timestamps
   - These are used by the sync process and don't need to be in Supabase

5. **Field Name Differences**:
   - Some fields have different names but serve the same purpose
   - Sync logic needs to map these correctly

## Recommended Schema Updates

### For SQLite:

```sql
-- Add client_created_at to tables that need it for sync timing
ALTER TABLE activity_logs ADD COLUMN client_created_at TIMESTAMP;
ALTER TABLE screenshots ADD COLUMN client_created_at TIMESTAMP;
```

### For Supabase:

No schema updates needed for Supabase as it already contains all the required columns for synchronization. The local SQLite database contains additional columns for tracking sync status and local functionality that don't need to be in Supabase.

## Synchronization Process

The synchronization process should:

1. **For uploads to Supabase**:
   - Convert local INTEGER IDs to UUIDs where needed or use existing UUIDs in TEXT fields
   - Add user_id and org_id to records being sent to Supabase
   - Convert boolean INTEGER values to true PostgreSQL booleans
   - Map local file paths to storage URLs
   - Convert timestamps to the right format
   - Mark records as synced in the local database

2. **For downloads from Supabase**:
   - Store UUIDs as TEXT in relevant tables
   - Map Supabase file URLs to local paths
   - Convert PostgreSQL booleans to INTEGER 0/1 values
   - Convert timestamps to SQLite format
   - Add sync status tracking columns with appropriate values
