# Supabase Storage Setup

The Dash dashboard can save uploaded CSV files to Supabase Storage. This makes the upload flow useful for shared deployments instead of only keeping data in memory.

## What is stored

- The raw uploaded CSV file is saved to Supabase Storage.
- The app still cleans the CSV and refreshes the dashboard immediately.
- The cleaned dashboard state is still held in server memory for the current running process.

## Create the bucket

1. Create a Supabase project.
2. Open Storage.
3. Create a private bucket named `riverkeeper-uploads`.
4. Keep the bucket private unless the client explicitly wants public file links.

## Configure environment variables

Create a local `.env` file or set these variables in your hosting provider:

```bash
SUPABASE_URL=https://bqwfuuzcmcfgywozszzx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=riverkeeper-uploads
SUPABASE_STORAGE_PREFIX=uploads
```

Use the service role key only on the server. Never put it in browser JavaScript.

## Run locally

```bash
cd "/Users/kevintang/Downloads/riverkeeper_project2-main 2"
export SUPABASE_URL="https://bqwfuuzcmcfgywozszzx.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
export SUPABASE_STORAGE_BUCKET="riverkeeper-uploads"
python3 -m dash_app.app
```

Then open:

```text
http://127.0.0.1:8050
```

## Expected behavior

When storage is configured, a successful upload shows a message like:

```text
Saved to Supabase Storage: uploads/20260425T120000Z-donor_data.csv
```

When storage is not configured, uploads still work for the current session and the dashboard shows that the data is session-only.

## Testing Uploads and Deletes

Use a small test CSV first. After upload, the dashboard should show the saved file under "Saved CSVs" below the upload box.

To remove an accidental upload, click "Delete" next to that CSV. Deletes are limited to `.csv` files inside the configured upload prefix, so the dashboard will refuse to delete unrelated bucket content.

You can also refresh the saved file list without uploading by clicking "Refresh uploads".

## Hosting note

For a multi-user nonprofit handoff, pair this with a persistent app host such as Render, Railway, or Fly.io. Vercel can run Python functions, but this Dash app is currently a long-running server with in-memory dashboard state, so a traditional Python app host is simpler.
