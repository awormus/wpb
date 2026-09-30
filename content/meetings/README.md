# Commission meetings — text archive + summaries

**Rule:** Store a **plain-text extract** of each official commission PDF here. Link the PDF on wpb.org. **Never** commit binary PDFs.

## Folder layout

```
content/meetings/
  README.md                 ← this file
  YYYY-MM-DD/               ← one folder per meeting date
    agenda.md               ← full text extract (+ YAML frontmatter)
    summary.md              ← short attributable summary (optional until minutes exist)
    minutes.md              ← text extract of minutes when published (optional)
    pass-fail.md            ← text extract of pass/fail sheet when published (optional)
```

Legacy single-file names (`YYYY-MM-DD-short-title.md`) are retired; migrate into dated folders.

## Frontmatter (agenda.md / minutes.md)

```yaml
---
date: 2026-09-28
doc_type: agenda   # agenda | minutes | pass-fail | other
title: Final City Commission Agenda
official_pdf: https://www.wpb.org/files/.../whatever.pdf
retrieved: YYYY-MM-DD
extractor: pdftotext -layout
---
```

## Workflow

1. Find the PDF on [Meetings & Agendas](https://www.wpb.org/Our-City/Meetings-Agendas) or [Commission & CRA Agendas](https://www.wpb.org/Our-City/City-Clerk/Commission-CRA-Agendas).
2. Download to `/tmp` only → `pdftotext -layout` → write `agenda.md` (or minutes) → **delete** the PDF from `/tmp`.
3. Write or refresh `summary.md` (agenda-based until minutes/pass-fail exist; never invent votes).
4. Log every external fetch in `ops/external-access-log.md`.
5. Add or update topic pages under `content/wiki/topics/` so the same ordinance/project can link across meeting dates.
6. Mirror a short HTML summary under `docs/commission/YYYY-MM-DD/` for the public site.

## Wiki

Cross-meeting insight lives in `content/wiki/` (index + topic pages). Meeting folders hold the verbatim extracts; wiki pages link **to** those extracts and to the official PDFs.
