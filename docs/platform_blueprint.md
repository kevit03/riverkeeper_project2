# Riverkeeper Single-Platform Blueprint

## What changed

The legacy Streamlit app is still in the repo for reference, but the recommended
client-facing direction is now the static web portal in
`client_portal/`. The geography heatmap is the strongest implemented slice in this pass.
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

The current deliverable already fits that pattern because the frontend only
needs `client_portal/` plus the exported `data/portal_analytics_data.json` file.

## Four workstreams

| Workstream | Scope | Deliverable | Shared contract |
| --- | --- | --- | --- |
| Geography | Geo intelligence and client heatmap | `client_portal/` geography tab, metric toggles, exported map payload | Shared portal analytics payload |
| Concentration | Donor concentration and trend analysis | Concentration view, top donor logic, state coverage, time trends | Shared portal analytics payload |
| Engagement | KPI and engagement layer | Active vs inactive KPIs, state engagement, cadence metrics | Shared portal analytics payload |
| Reporting | Reporting and stakeholder handoff | Segment tables, giving-by-size summaries, board-ready reporting tables | Shared portal analytics payload |

## Implementation instructions for the remaining team members

### Concentration

- Build `/ingest` as the upload flow for non-technical clients.
- Validate required CSV columns before any processing starts.
- Return plain-English errors when uploads fail.
- Trigger the cleaning pipeline and regenerate the shared exported JSON payload after a successful upload.
- Done when a client can upload a valid file and refresh the portal data without developer help.

### Engagement

- Build `/analytics` as the deeper analysis workspace.
- Use the cleaned donor dataset to show donor tiers, active vs inactive segments, lapsed-donor views, and state-level performance.
- Reuse the existing filtering language from the portal so the product feels consistent.
- Keep charts presentation-ready and avoid raw developer-style tables unless they add clear value.
- Done when leadership can answer which regions are strongest, which are slipping, and where follow-up should happen next.

### Reporting

- Build `/reports` for export and stakeholder handoff.
- Add board-ready summaries, filtered exports, and CRM-friendly downloads.
- Support report generation from the same active filters used in the portal.
- Make outputs usable outside the app without manual spreadsheet cleanup.
- Done when a client can leave the platform with a usable summary or export in one step.

## Suggested route map

- `/heatmap`
  The current live route. This is already represented by `client_portal/index.html`.
- `/ingest`
  Upload and validation experience for non-technical client users.
- `/analytics`
  Summary dashboards, concentration analysis, and donor segmentation views.
- `/reports`
  Exports, stakeholder reports, and CRM handoff tools.

## File handoff for another company

- `app/data/donor_data_enriched.csv`
  Current cleaned source of truth used for the geography implementation.
- `app/functions/portal_analytics_export.py`
  Converts the cleaned CSV into a frontend-ready JSON payload for all portal tabs.
- `client_portal/`
  Deployable frontend assets for the heatmap slice.

## Naming note

The client-facing platform is now described by workstream instead of individual contributor.
The older folder names remain in `scripts/` only so the original source material is still traceable.
