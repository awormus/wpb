# Commission meetings — text archive + summaries

**Rule:** Store a **plain-text / markdown extract** of each official commission PDF here. Link the PDF on wpb.org. **Never** commit binary PDFs.

Extracts follow the **civic-pdf-to-markdown** standard (skill: `/home/box/agent-data/workflows/civic-pdf-to-markdown/SKILL.md`), applied via `ops/civic_pdf_cleanup.py`. Goal: readable markdown with **stable `#item-*` anchors** for summaries and wiki deep-links — not raw `pdftotext` soup.

## Folder layout

```
content/meetings/
  README.md                 ← this file
  YYYY-MM-DD/               ← one folder per meeting date
    agenda.md               ← normalized extract (+ YAML frontmatter + item anchors)
    summary.md              ← short attributable summary (optional until minutes exist)
    minutes.md              ← text extract of minutes when published (optional)
    pass-fail.md            ← normalized pass/fail extract when published (optional)
```

Legacy single-file names (`YYYY-MM-DD-short-title.md`) are retired; migrate into dated folders.

## Frontmatter (agenda.md / minutes.md / pass-fail.md)

```yaml
---
date: 2026-09-28
doc_type: agenda   # agenda | minutes | pass-fail | other
title: Final City Commission Agenda
meeting: Regular City Commission Meeting
official_pdf: https://www.wpb.org/files/.../whatever.pdf
retrieved: YYYY-MM-DD
extractor: pdftotext (prefer no -layout; flatten in cleanup) + civic-pdf-cleanup
---
```

## Normalized body

1. Form-feeds → blank line; `Page N of M` and repeating running headers stripped.
2. PDF bullet glyphs → `- `.
3. Whitespace collapsed (trim; 3+ blanks → 2); item numbers kept intact.
4. H1 title + official PDF link + HR + body.
5. Agenda items promoted to headings with stable HTML anchors:
   - `N.` → `## N. Title` with `<a id="item-N"></a>`
   - `N.M.` → `### N.M. Title` with `<a id="item-N-M"></a>`
   - `N.A.` → `<a id="item-N-A"></a>`
6. Anchor ids: lowercase digits/hyphens only. **Never rename after publish** — wiki links depend on them.
7. Pass/fail sheets use the same `item-*` scheme where numbers exist.

## Workflow

1. Find the PDF on [Meetings & Agendas](https://www.wpb.org/Our-City/Meetings-Agendas) or [Commission & CRA Agendas](https://www.wpb.org/Our-City/City-Clerk/Commission-CRA-Agendas).
2. Download to `/tmp` only → `pdftotext (prefer no -layout; flatten in cleanup)` → run `ops/civic_pdf_cleanup.py` → write `agenda.md` (or minutes / pass-fail) → **delete** the PDF from `/tmp`.
3. Write or refresh `summary.md` (agenda-based until minutes/pass-fail exist; never invent votes). Prefer deep-links like `[9.1 Mobility Plan](./agenda.md#item-9-1)`.
4. Log every external fetch in `ops/external-access-log.md`.
5. Add or update topic pages under `content/wiki/topics/` so the same ordinance/project can link across meeting dates (include `#item-…` when the mapping is clear).
6. Mirror a short HTML summary under `docs/commission/YYYY-MM-DD/` for the public site.

## Wiki

Cross-meeting insight lives in `content/wiki/` (index + topic pages). Meeting folders hold the verbatim extracts; wiki pages link **to** those extracts (ideally `#item-*`) and to the official PDFs.
