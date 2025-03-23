# Setting Up the Screenshots Bucket in Supabase - Secure Configuration

The TimeTracker application needs a storage bucket named "screenshots" in your Supabase project. Because screenshots may contain sensitive information, we'll create a private bucket with proper security policies:

## 1. Access the Supabase Dashboard

Go to [app.supabase.com](https://app.supabase.com) and log in to your account.

## 2. Select Your Project

Select the project you're using for TimeTracker (the one whose URL and key you've configured in your `.env` file).

## 3. Navigate to Storage

In the left sidebar menu, click on **Storage**.

## 4. Create a New Bucket

1. Click the **Create a new bucket** button
2. Enter `screenshots` as the bucket name (this name is required - it must match exactly)
3. Toggle **Public bucket** to OFF (this is critical for security)
4. Click **Create bucket**

## 5. Configure Bucket Policies

After creating the bucket, you need to set up the right bucket policies:

1. Click on the `screenshots` bucket to open it
2. Click on the **Policies** tab
3. Click **Add Policy** and select **Customize policy**
4. Create the following policies:

   a. **For reading files**:
   - **Name**: Allow users to read their own screenshots
   - **Allowed operations**: SELECT
   - **Policy definition**: `(auth.uid() = owner) OR (auth.uid() IN (SELECT user_id FROM org_members WHERE org_id IN (SELECT org_id FROM org_members WHERE user_id = owner AND role = 'admin')))`
   - **Comment**: This allows users to read only their own files, or admins to read files from users in their organization
   - Click **Save policy**

   b. **For uploading files**:
   - **Name**: Allow authenticated uploads
   - **Allowed operations**: INSERT
   - **Policy definition**: `(auth.role() = 'authenticated')`
   - **Comment**: Only authenticated users can upload files
   - Click **Save policy**

   c. **For modifying files**:
   - **Name**: Allow users to modify their own files
   - **Allowed operations**: UPDATE
   - **Policy definition**: `(auth.uid() = owner)`
   - **Comment**: Users can only modify their own files
   - Click **Save policy**

   d. **For deleting files**:
   - **Name**: Allow users to delete their own files
   - **Allowed operations**: DELETE
   - **Policy definition**: `(auth.uid() = owner)`
   - **Comment**: Users can only delete their own files
   - Click **Save policy**

## 6. Verify Your Setup

After creating the bucket with appropriate permissions, run the test script:

```bash
python test_supabase_sync.py
```

The script should be able to authenticate and initialize the sync service without errors.

## Troubleshooting

If you encounter errors like:
- "Bucket not found": Ensure your bucket is named exactly "screenshots" (case-sensitive)
- Permission errors: Check your bucket policies to ensure authenticated users have write access
- Authentication issues: Confirm your Supabase URL and key are correctly set in your .env file

Remember that the service role key in your .env file gives your application higher privileges, which is useful for testing but should be handled carefully in production.
