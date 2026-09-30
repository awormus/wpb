# External access log

**Rule:** Every external read of city websites, agendas, packets, minutes, livestreams, or related public portals **must** be logged here. We are **read-only**: never write to, post on, authenticate against, or otherwise modify city systems.

## How to log

Add a new row (newest first) for each fetch:

| Date (ET) | Agent / person | URL or portal | Purpose | Notes |
|-----------|----------------|---------------|---------|-------|
| 2026-09-30 15:35 ET | Riley (WPB Data) | `https://api.censusreporter.org/1.0/data/show/latest?table_ids=B01003,B19013,B25001,B01002&geo_ids=16000US1276600` | ACS demographics for West Palm Beach city | Read-only GET; HTTP 200; ACS 2024 1-year; pop 127733, median age 41.6, median HH income 74478, housing units 64847 |
| 2026-09-30 15:35 ET | Riley (WPB Data) | `https://api.censusreporter.org/1.0/data/show/latest?table_ids=B03002,B25003,B17001,B15003,B25077,B23025&geo_ids=16000US1276600` | Additional ACS tables (race/ethnicity, tenure, poverty, education, home value, labor) | Read-only GET; HTTP 200; ACS 2024 1-year |
| 2026-09-30 15:35 ET | Riley (WPB Data) | `https://data.census.gov/profile/West_Palm_Beach_city,_Florida?g=160XX00US1276600` | Confirm city profile page exists | Read-only GET; HTTP 200; profile HTML shell (SPA); metrics taken from Census Reporter, not scraped from this page |
| 2026-09-30 15:35 ET | Riley (WPB Data) | `https://api.census.gov/data/202{2,3,4}/acs/acs5?...&for=place:76600&in=state:12` | Attempt direct Census API ACS 5-year | Read-only GET; redirected to Missing Key page — no key configured; no data used from this attempt |
| 2026-09-30 15:35 ET | Riley (WPB Data) | `https://api.censusreporter.org/1.0/data/show/acs2023_5yr?...&geo_ids=16000US1276600` | Prefer ACS 5-year if available | Read-only GET; HTTP 404 — release not available on this endpoint; used ACS 2024 1-year instead |


## Notes

- Prefer official City of West Palm Beach domains and linked agenda systems.
- Record enough detail that another editor can reproduce the read.
- Do not store credentials, session cookies, or private data in this log.
