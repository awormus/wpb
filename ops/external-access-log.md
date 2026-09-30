# External access log

**Rule:** Every external read of city websites, agendas, packets, minutes, livestreams, or related public portals **must** be logged here. We are **read-only**: never write to, post on, authenticate against, or otherwise modify city systems.

## How to log

Add a new row (newest first) for each fetch:

| Date (ET) | Agent / person | URL or portal | Purpose | Notes |
|-----------|----------------|---------------|---------|-------|
| 2026-09-30 15:56 ET | Riley (WPB Data) | `https://www.wpb.org/files/.../09_23_26-special-commission-agenda_budget-millage-final.pdf` | Backfill Sep 23 special agenda text | Read-only GET to /tmp; HTTP 200; 135284 bytes; pdftotext → content/meetings/2026-09-23/agenda.md; PDF deleted |
| 2026-09-30 15:56 ET | Riley (WPB Data) | `https://www.wpb.org/files/.../09_14_26_final-city-commission-agenda.pdf` | Backfill Sep 14 regular agenda text | Read-only GET to /tmp; HTTP 200; 308195 bytes; pdftotext → content/meetings/2026-09-14/agenda.md; PDF deleted |
| 2026-09-30 15:56 ET | Riley (WPB Data) | `https://www.wpb.org/files/.../09_08_26-special-commission-agenda_budget-millage-tenttive.pdf` | Backfill Sep 8 special agenda text | Read-only GET to /tmp; HTTP 200; 153154 bytes; pdftotext → content/meetings/2026-09-08/agenda.md; PDF deleted |
| 2026-09-30 15:54 ET | Riley (WPB Data) | `https://www.wpb.org/files/.../09_28_26_final-city-commission-agenda.pdf` | Re-fetch for in-repo text extract | Read-only GET to /tmp; HTTP 200; 284039 bytes; pdftotext → `content/meetings/2026-09-28/agenda.md`; PDF deleted; not committed |
| 2026-09-30 15:42 ET | Riley (WPB Data) | `https://www.wpb.org/Our-City/Meetings-Agendas` | List meetings / WML links | Read-only GET; HTTP 200; identified WML PDFs and upcoming Commission dates |
| 2026-09-30 15:42 ET | Riley (WPB Data) | `https://www.wpb.org/files/.../wml_2026-0928-1002_final.pdf` | Weekly Meeting List Sep 28–Oct 2 | Read-only GET to /tmp; HTTP 200; text extracted with pdftotext; PDF not stored in repo; deleted after use |
| 2026-09-30 15:42 ET | Riley (WPB Data) | `https://www.wpb.org/files/.../wml_2026-0921-0925_revision1.pdf` | Weekly Meeting List Sep 21–25 | Read-only GET to /tmp; HTTP 200; extracted; PDF not stored in repo |
| 2026-09-30 15:42 ET | Riley (WPB Data) | `https://www.wpb.org/Our-City/City-Clerk/Commission-CRA-Agendas` | Find Commission agenda indexes | Read-only GET; HTTP 200 |
| 2026-09-30 15:42 ET | Riley (WPB Data) | `https://www.wpb.org/.../2026-City-Commission-Agendas` | 2026 Commission agenda months | Read-only GET; HTTP 200 |
| 2026-09-30 15:42 ET | Riley (WPB Data) | `https://www.wpb.org/.../September-2026` | September 2026 agenda PDF list | Read-only GET; HTTP 200; located Sep 28 FINAL agenda PDF |
| 2026-09-30 15:42 ET | Riley (WPB Data) | `https://www.wpb.org/.../October-2026` | Check for Oct 13 agenda PDF | Read-only GET; HTTP 200; no Commission agenda PDFs listed yet |
| 2026-09-30 15:42 ET | Riley (WPB Data) | `https://www.wpb.org/files/.../09_28_26_final-city-commission-agenda.pdf` | Summarize most recent Commission meeting | Read-only GET to /tmp only; HTTP 200; 284039 bytes; pdftotext; **PDF not committed**; deleted after summary |
| 2026-09-30 15:35 ET | Riley (WPB Data) | `https://api.censusreporter.org/1.0/data/show/latest?table_ids=B01003,B19013,B25001,B01002&geo_ids=16000US1276600` | ACS demographics for West Palm Beach city | Read-only GET; HTTP 200; ACS 2024 1-year; pop 127733, median age 41.6, median HH income 74478, housing units 64847 |
| 2026-09-30 15:35 ET | Riley (WPB Data) | `https://api.censusreporter.org/1.0/data/show/latest?table_ids=B03002,B25003,B17001,B15003,B25077,B23025&geo_ids=16000US1276600` | Additional ACS tables (race/ethnicity, tenure, poverty, education, home value, labor) | Read-only GET; HTTP 200; ACS 2024 1-year |
| 2026-09-30 15:35 ET | Riley (WPB Data) | `https://data.census.gov/profile/West_Palm_Beach_city,_Florida?g=160XX00US1276600` | Confirm city profile page exists | Read-only GET; HTTP 200; profile HTML shell (SPA); metrics taken from Census Reporter, not scraped from this page |
| 2026-09-30 15:35 ET | Riley (WPB Data) | `https://api.census.gov/data/202{2,3,4}/acs/acs5?...&for=place:76600&in=state:12` | Attempt direct Census API ACS 5-year | Read-only GET; redirected to Missing Key page — no key configured; no data used from this attempt |
| 2026-09-30 15:35 ET | Riley (WPB Data) | `https://api.censusreporter.org/1.0/data/show/acs2023_5yr?...&geo_ids=16000US1276600` | Prefer ACS 5-year if available | Read-only GET; HTTP 404 — release not available on this endpoint; used ACS 2024 1-year instead |


## Notes

- Prefer official City of West Palm Beach domains and linked agenda systems.
- Record enough detail that another editor can reproduce the read.
- Do not store credentials, session cookies, or private data in this log.
