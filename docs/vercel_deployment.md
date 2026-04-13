# Riverkeeper Portal: Vercel Deployment

## What should be deployed

Deploy the static presentation shell in `client_portal/`.

That gives you:

- Kevin's implemented geography heatmap
- The simplified overview shell
- Placeholder analytics and delivery tabs that can be filled in later

Do not deploy the legacy Streamlit app for the client presentation.

## How the current pieces fit together

The cleanest single-platform setup is:

1. `client_portal/`
   This is the client-facing frontend.
2. `app/functions/heatmap_portal_export.py`
   This generates Kevin's heatmap payload.
3. `scripts/aarit/donor_analysis.py`
   Keep this as analysis logic that should later feed the `Analytics` tab.
4. `scripts/daniel/daniel.py`
   Keep this as KPI logic that should later feed summary cards and state-level tables.
5. `scripts/aishwarya/test`
   Keep this as reporting and donor segmentation logic that should later feed export-ready views.

Right now, only Kevin's geography flow is presentation-ready. The other three scripts should be treated as backend analysis sources, not as standalone client experiences.

## Best way to combine the new changes

Use the portal as the single frontend and convert everyone else's work into data outputs:

- Kevin
  Owns the geography experience already live in the portal.
- Aarit
  Should output cleaned segmentation tables or JSON for donor category views.
- Daniel
  Should output KPI summaries and active-versus-inactive metrics as JSON.
- Aishwarya
  Should output report tables, charts, and export-ready files into a predictable folder.

Recommended shared contract:

- `client_portal/data/kevin_heatmap_data.json`
- `client_portal/data/daniel_kpis.json`
- `client_portal/data/aarit_segments.json`
- `client_portal/data/aishwarya_reports.json`

That keeps one presentation surface while allowing each workstream to stay separate.

## Pre-deploy step

From the repo root, regenerate Kevin's payload before deploying:

```bash
python3 app/functions/heatmap_portal_export.py
```

## Vercel project settings

When importing the repo into Vercel:

- Framework Preset: `Other`
- Root Directory: `client_portal`
- Build Command: leave empty
- Output Directory: `.`

## Deploy options

### Option 1: Vercel dashboard

1. Push the repo to GitHub.
2. Import the repository into Vercel.
3. Set the root directory to `client_portal`.
4. Deploy.

### Option 2: Vercel CLI

From the repo root:

```bash
npx vercel --cwd client_portal
```

For production:

```bash
npx vercel --prod --cwd client_portal
```

## Cost note

For a client presentation, this should typically fit on Vercel's free tier because the deployed asset is a static site.

Costs would start to matter later if you add:

- scheduled ingestion jobs
- server-side APIs
- authenticated user accounts
- database-backed analytics

## Recommendation

For the presentation:

- deploy only `client_portal/`
- treat Kevin's geography tab as the live implementation
- describe Daniel, Aarit, and Aishwarya's work as the next data layers to be wired into the same portal

That gives the nonprofit one clean URL and avoids exposing half-finished standalone scripts.
