# Riverkeeper Portal: Vercel Deployment

## What should be deployed

Deploy the static presentation shell in `client_portal/`.

That gives you:

- the implemented geography heatmap
- The simplified overview shell
- Placeholder analytics and delivery tabs that can be filled in later

Do not deploy the legacy Streamlit app for the client presentation.

## How the current pieces fit together

The cleanest single-platform setup is:

1. `client_portal/`
   This is the client-facing frontend.
2. `app/functions/portal_analytics_export.py`
   This generates the combined client portal payload, including the geography layer.
3. Legacy analysis scripts under `scripts/`
   Keep these as the upstream source material for concentration, KPI, and reporting logic now surfaced through the portal.

Right now, the geography flow is the strongest presentation-ready slice. The other three scripts should be treated as backend analysis sources, not as standalone client experiences.

## Best way to combine the new changes

Use the portal as the single frontend and convert each workstream into data outputs:

- Geography
  Owns the map experience already live in the portal.
- Concentration and trends
  Outputs donor concentration, state coverage, and time-series views.
- Engagement KPIs
  Outputs KPI summaries and active-versus-inactive metrics.
- Reporting
  Outputs report tables, charts, and export-ready files into a predictable folder.

Recommended shared contract:

- `client_portal/data/portal_analytics_data.json`

That keeps one presentation surface while allowing each workstream to stay separate behind a single frontend payload.

## Pre-deploy step

From the repo root, regenerate the combined payload before deploying:

```bash
python3 app/functions/portal_analytics_export.py
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
- keep geography as the live map implementation
- surface engagement KPIs in Overview and Analytics
- surface concentration and trend analysis in Analytics
- surface segmentation and report tables in Reports

That gives the nonprofit one clean URL and avoids exposing half-finished standalone scripts.
