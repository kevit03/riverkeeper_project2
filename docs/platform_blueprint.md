# Riverkeeper Single-Platform Blueprint

## What changed

The legacy Streamlit app is still in the repo for reference, but the recommended
client-facing direction is now the static web portal in
`client_portal/`. Kevin's heatmap is the only implemented slice in this pass.
Everything else is intentionally divided into clearly scoped workstreams so a
future team or outside company can keep building on one platform instead of
rewriting the project.

## Why this is a better client option than Streamlit

- The client experience is a branded web page, not a developer tool UI.
- The heatmap is driven by one exported JSON payload, so another company can
  replace the dataset without learning the original notebook-style flow.
- Static assets are easier to host, cache, white-label, and hand off than a
  Streamlit process.
- The frontend can scale independently from the cleaning and enrichment logic.

## One-platform implementation pattern

Use one platform that supports these four capabilities under the same vendor:

1. Static asset hosting for the portal frontend
2. Container or function execution for ingestion and enrichment jobs
3. Object storage for CSV uploads and generated exports
4. Managed database or scheduled job support for long-term reporting

Kevin's current deliverable already fits that pattern because the frontend only
needs `client_portal/` plus the exported `data/kevin_heatmap_data.json` file.

## Four workstreams

| Owner | Scope | Deliverable | Shared contract |
| --- | --- | --- | --- |
| Kevin | Geo intelligence and client heatmap | `client_portal/` heatmap, metric toggles, exported map payload | `client_portal/data/kevin_heatmap_data.json` |
| Aarit | Ingestion and validation | Upload wizard, schema checks, job progress, clean error states | Cleaned donor CSV and job status endpoint |
| Daniel | Analytics and segmentation | KPI dashboard, donor tiers, geography tables, retention metrics | Read-only analytics payloads from cleaned data |
| Aishwarya | Reporting and stakeholder handoff | Scheduled exports, executive summaries, CRM-ready downloads | Reporting endpoints and export templates |

## Implementation instructions for the remaining team members

### Aarit

- Build `/ingest` as the upload flow for non-technical clients.
- Validate required CSV columns before any processing starts.
- Return plain-English errors when uploads fail.
- Trigger the cleaning pipeline and regenerate Kevin's exported JSON payload after a successful upload.
- Done when a client can upload a valid file and refresh the portal data without developer help.

### Daniel

- Build `/analytics` as the deeper analysis workspace.
- Use the cleaned donor dataset to show donor tiers, active vs inactive segments, lapsed-donor views, and state-level performance.
- Reuse the existing filtering language from Kevin's portal so the product feels consistent.
- Keep charts presentation-ready and avoid raw developer-style tables unless they add clear value.
- Done when leadership can answer which regions are strongest, which are slipping, and where follow-up should happen next.

### Aishwarya

- Build `/reports` for export and stakeholder handoff.
- Add board-ready summaries, filtered exports, and CRM-friendly downloads.
- Support report generation from the same active filters used in the portal.
- Make outputs usable outside the app without manual spreadsheet cleanup.
- Done when a client can leave the platform with a usable summary or export in one step.

## Suggested route map

- `/heatmap`
  Kevin's live route. This is already represented by `client_portal/index.html`.
- `/ingest`
  Aarit's upload and validation experience for non-technical client users.
- `/analytics`
  Daniel's summary dashboards and donor segmentation views.
- `/reports`
  Aishwarya's exports, stakeholder reports, and CRM handoff tools.

## File handoff for another company

- `app/data/donor_data_enriched.csv`
  Current cleaned source of truth used for Kevin's implementation.
- `app/functions/heatmap_portal_export.py`
  Converts the cleaned CSV into a frontend-ready JSON payload.
- `client_portal/`
  Deployable frontend assets for the heatmap slice.

## Naming update

The forward-looking ownership model is now:

- Kevin
- Aarit
- Daniel
- Aishwarya

The older student folder names remain in `scripts/` only so the original source
material is still traceable.
