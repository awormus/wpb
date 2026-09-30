# West Palm Beach Civic Brief (`awormus/wpb`)

Public-facing static site for **West Palm Beach** city data: demographics, City Commission meeting summaries, and a civic calendar. Hosted cheaply on **GitHub Pages** from the `/docs` folder.

**Site:** https://awormus.github.io/wpb/

## Isolation rule

This repository is **only** for WPB civic content.

- Work under `/home/box/wpb` (this clone).
- **Never** mix with `awormus/crew` or `/workspace`. Do not read, write, or `cd` into the crew tree for WPB work, and do not put WPB files in crew.

## Site map (`docs/`)

| Path | Purpose |
|------|---------|
| `docs/index.html` | Home — what the site is; links to sections |
| `docs/demographics/` | Census/ACS stats (placeholder until data lands) |
| `docs/commission/` | Index of meeting summaries |
| `docs/calendar/` | Calendar page; points to ICS |
| `docs/calendar.ics` | **Published** ICS feed (“West Palm Beach City”) — single source for Pages |
| `docs/about/` | About + methodology |
| `docs/styles.css` | Shared civic stylesheet |

## Content (`content/`)

| Path | Purpose |
|------|---------|
| `content/demographics.json` | Schema stub + empty `metrics` / `sources` |
| `content/meetings/` | One markdown file per meeting (`YYYY-MM-DD-title.md` + frontmatter) |
| `content/calendar.ics` | Working draft copy of the ICS (keep in sync with `docs/calendar.ics`; **Pages serves `docs/calendar.ics`**) |

## Ops (`ops/`)

- `external-access-log.md` — log **every** external read of city sites/agendas; never write to city systems.
- `README.md` — team/agent ops notes.

## How agents update content

1. Stay inside this repo only.
2. Edit `content/` for structured data and meeting notes; update matching HTML under `docs/`.
3. For the calendar: edit `docs/calendar.ics` (canonical for GitHub Pages) and mirror to `content/calendar.ics` if you use the draft copy.
4. Append a row to `ops/external-access-log.md` for each external fetch.
5. Cite sources on the page and in meeting frontmatter.
6. `git add`, commit, `git push origin main`. No build step, no npm.

## GitHub Pages

- Source: branch **`main`**, folder **`/docs`**.
- Stack: vanilla HTML + CSS only.

## License / stance

Not an official City of West Palm Beach site. Public sources only; read-only; cite everything.
