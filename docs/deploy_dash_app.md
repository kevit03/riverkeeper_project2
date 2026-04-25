# Deploying the Dash Dashboard

The current production-ready path is Render. This app is a Python Dash server, so it needs a web host that can run a long-lived Python process and bind to `0.0.0.0:$PORT`.

## Render

1. Push this branch to GitHub.
2. In Render, create a new Blueprint from the repo, or create a Web Service manually.
3. Use branch `aarit-frontend`.
4. Use this build command:

```bash
pip install -r requirements-dash.txt
```

5. Use this start command:

```bash
gunicorn dash_app.app:server --bind 0.0.0.0:$PORT
```

6. Add these environment variables:

```bash
SUPABASE_URL=https://bqwfuuzcmcfgywozszzx.supabase.co
SUPABASE_STORAGE_BUCKET=riverkeeper-uploads
SUPABASE_STORAGE_PREFIX=uploads
SUPABASE_SERVICE_ROLE_KEY=<paste this in Render only>
```

Do not commit the service role key. Keep it only in Render's environment variables and in your local `.env` file.

## Why Not Vercel For This Version

Vercel is best if this becomes a Next.js dashboard with API routes. The current app is Dash, which is designed to run as a Python web server. Render or Railway can host that directly with fewer changes.

## Local Fallback

You can still run the same app locally:

```bash
python3 -m dash_app.app
```

Then open:

```text
http://127.0.0.1:8050
```
