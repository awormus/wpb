# Meeting summaries

One markdown file per City Commission (or related) meeting.

## Naming

```
YYYY-MM-DD-short-title.md
```

Examples:

- `2026-01-15-regular-commission.md`
- `2026-02-03-special-workshop.md`

## Frontmatter

Each file starts with YAML frontmatter:

```yaml
---
date: 2026-01-15
title: Regular City Commission Meeting
sources:
  - title: Official agenda
    url: https://example.city/agenda/...
    retrieved: 2026-01-16
  - title: Meeting minutes
    url: https://example.city/minutes/...
    retrieved: 2026-01-20
---
```

## Body

Write a short, attributable summary. Quote sparingly; prefer paraphrase with clear citations. Do not invent votes or outcomes. Log every external fetch in `ops/external-access-log.md`.

Published HTML for the commission index lives under `docs/commission/` and should link here when summaries exist.
