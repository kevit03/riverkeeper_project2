# Feature Brainstorm From The Cleaned Donor Data

This brainstorm is based on the current cleaned file at
`app/data/donor_data_enriched.csv`.

## What the data already supports

- 7,275 donor records with mapped coordinates
- 2,815 active donors based on gifts in the last 18 months
- $49.55M in lifetime donations
- 1,187 mapped location clusters after coordinate rounding
- 42 covered states, with New York driving most donor density

## Strong next additions

- Retention risk layer
  Surface high-value donors or high-value clusters with zero gifts in the last
  18 months.

- Major donor density toggle
  Keep the current count-based heatmap, but add a second lens focused on total
  dollars instead of donor count.

- Regional ambassador finder
  Highlight towns or neighborhoods with strong donor density and healthy active
  rates for event planning or volunteer recruiting.

- State expansion scorecard
  Compare states by donor count, lifetime giving, and active donor share to
  identify where Riverkeeper already has momentum outside New York.

- Local event radius planning
  Combine clustered donors with county and city labels to decide where in-person
  events are most likely to pull attendance.

- Lapsed major donor watchlist
  Build a filtered export for donors with high lifetime value but no recent
  giving, sorted by geography for targeted outreach.

- Executive territory snapshots
  Generate one-click summaries for board members or fundraisers covering the
  donors, active share, and giving totals in a selected state or county.

- Data quality monitoring
  Track coordinate anomalies, blank county fields, city normalization issues,
  and unusually large donation outliers before they reach client reports.

- Campaign segmentation
  Build donor cohorts using only fields already present: lifetime giving, gift
  recency proxy, and geography.

- Coverage gap detector
  Show places with meaningful donor count but weak recent activity so Riverkeeper
  can decide whether those communities need events, stewardship, or a different
  campaign.

## Best first follow-ups after the geography slice

- Build a guided upload and validation page so the heatmap payload is
  regenerated without developer involvement.
- Turn the same cleaned dataset into segment dashboards and trend
  summaries.
- Package filtered exports and stakeholder-ready reports on top of
  those same payloads.
