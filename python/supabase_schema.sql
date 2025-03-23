-- Supabase SQL Schema for TimeTracker Application
-- This script creates the necessary tables in your Supabase project
-- to work with the TimeTracker application sync functionality.

-- Organizations Table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Organization Members Table
CREATE TABLE IF NOT EXISTS org_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'member', -- Options: 'admin', 'member', etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(org_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON org_members(user_id);

-- Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(id),
    window_title TEXT NOT NULL,
    process_name TEXT NOT NULL,
    executable_path TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    client_created_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_org_id ON activity_logs(org_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_start_time ON activity_logs(start_time);

-- Screenshots Table
CREATE TABLE IF NOT EXISTS screenshots (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(id),
    activity_log_id BIGINT REFERENCES activity_logs(id),
    image_url TEXT NOT NULL,
    thumbnail_url TEXT,
    taken_at TIMESTAMPTZ NOT NULL,
    client_created_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_screenshots_user_id ON screenshots(user_id);
CREATE INDEX IF NOT EXISTS idx_screenshots_org_id ON screenshots(org_id);
CREATE INDEX IF NOT EXISTS idx_screenshots_activity_log_id ON screenshots(activity_log_id);
CREATE INDEX IF NOT EXISTS idx_screenshots_taken_at ON screenshots(taken_at);

-- Row Level Security Policies
-- These ensure that users can only access data from their organization

-- Organizations RLS
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their organizations" 
ON organizations FOR SELECT 
USING (
    id IN (
        SELECT org_id FROM org_members 
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Admins can insert organizations" 
ON organizations FOR INSERT 
WITH CHECK (
    id IN (
        SELECT org_id FROM org_members 
        WHERE user_id = auth.uid() AND role = 'admin'
    )
);

CREATE POLICY "Admins can update organizations" 
ON organizations FOR UPDATE 
USING (
    id IN (
        SELECT org_id FROM org_members 
        WHERE user_id = auth.uid() AND role = 'admin'
    )
);

-- Org Members RLS
ALTER TABLE org_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view members in their organizations" 
ON org_members FOR SELECT 
USING (
    org_id IN (
        SELECT org_id FROM org_members 
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Admins can insert members" 
ON org_members FOR INSERT 
WITH CHECK (
    org_id IN (
        SELECT org_id FROM org_members 
        WHERE user_id = auth.uid() AND role = 'admin'
    )
);

CREATE POLICY "Users can insert themselves as members" 
ON org_members FOR INSERT 
WITH CHECK (
    user_id = auth.uid()
);

-- Activity Logs RLS
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own activity logs" 
ON activity_logs FOR SELECT 
USING (
    user_id = auth.uid() OR
    org_id IN (
        SELECT org_id FROM org_members 
        WHERE user_id = auth.uid() AND role = 'admin'
    )
);

CREATE POLICY "Users can insert their own activity logs" 
ON activity_logs FOR INSERT 
WITH CHECK (
    user_id = auth.uid() AND
    org_id IN (
        SELECT org_id FROM org_members 
        WHERE user_id = auth.uid()
    )
);

-- Screenshots RLS
ALTER TABLE screenshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own screenshots" 
ON screenshots FOR SELECT 
USING (
    user_id = auth.uid() OR
    org_id IN (
        SELECT org_id FROM org_members 
        WHERE user_id = auth.uid() AND role = 'admin'
    )
);

CREATE POLICY "Users can insert their own screenshots" 
ON screenshots FOR INSERT 
WITH CHECK (
    user_id = auth.uid() AND
    org_id IN (
        SELECT org_id FROM org_members 
        WHERE user_id = auth.uid()
    )
);

-- Sample Data: Create a default organization for testing
INSERT INTO organizations (name, settings)
VALUES ('Test Organization', '{"timezone": "UTC"}')
ON CONFLICT DO NOTHING;

-- Add yourself as an admin (manually add your Supabase user ID after signing up)
-- INSERT INTO org_members (org_id, user_id, role)
-- VALUES 
--   ((SELECT id FROM organizations WHERE name = 'Test Organization'), 'YOUR-SUPABASE-USER-ID', 'admin');
