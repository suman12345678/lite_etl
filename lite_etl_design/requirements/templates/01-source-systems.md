# 01 - Source systems

> One block per source. Copy the block as many times as needed.

## Summary

| Slug | Type | Mode | Volume/day | Cadence | Owner |
|------|------|------|-----------|---------|-------|
| | sql / csv / bigquery / api / sftp / object-store / stream | full / incremental / cdc / file-arrival | | | |

---

## Source: `<slug>`

- **Subject area / domain:**
- **System of record:**
- **Type:** `sql` (engine: ) | `csv` | `bigquery` | `rest_api` | `sftp` | `object storage` | `streaming` | other
- **How we reach it:** host / URL / bucket / dataset / table / query / file glob
  _(no credentials here - describe the location only)_
- **Auth method (reference, not value):** env var `` / secret-manager path `` / key file `` / IAM role `` / OAuth
- **Objects to extract:** table list / SQL / endpoints / file pattern
- **Extract mode:** full | incremental | cdc | file-arrival
- **Watermark column (if incremental):** name, type, timezone
- **Expected volume:** rows/day, GB/day, file count; peak vs average
- **Source freshness:** how current is the data; acceptable lag
- **Format & encoding:** delimiter, header?, encoding, date/number formats, null token
- **Known quirks:** trailing spaces, mixed types, partial files, late data,
  duplicate deliveries, schema drift, timezone traps
- **Sample / data dictionary available?** (if yes, place it in the workspace's `intake/`)
- **Downstream use:** which target table(s) / consumers

---

## Cross-source notes

- Shared connections (one profile reused by several sources):
- Sources that must be extracted together / in a fixed order:
