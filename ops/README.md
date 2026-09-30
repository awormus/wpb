# Ops — West Palm Beach Civic Brief

Notes for the WPB team and agents working in `awormus/wpb`.

## Isolation

- Work **only** in this repository (`/home/box/wpb` on the shared box).
- **Never** mix with `awormus/crew` or `/workspace`. Different purpose, different git remote.

## Hosting

- Static site under `docs/`, served by **GitHub Pages** from the `main` branch `/docs` folder.
- Public URL: https://awormus.github.io/wpb/

## Content workflow

1. Update structured data in `content/` (demographics JSON, meeting markdown, calendar draft if used).
2. Reflect changes in corresponding pages under `docs/`.
3. Keep `docs/calendar.ics` as the published ICS (single source for Pages); sync from `content/calendar.ics` if you edit the draft copy.
4. Log every external city/agenda read in `external-access-log.md`.
5. Commit on `main` and push; Pages rebuilds from `/docs`.

## Safety

- Public sources only; cite on every page and in frontmatter.
- Read-only toward city systems — no forms, no posts, no auth.
- No secrets in the repo.
