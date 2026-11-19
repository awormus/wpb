# Scoping: Palm Beach County Board of County Commissioners (BCC) votes, Nov 2018 – Nov 2026

Status: SCOPING ONLY (Riley, 2026-11-19, ~08:12–08:36 EST). Nothing in this note has been ingested into the site.
Every fetch behind it is listed in `ops/external-access-log.md` (2026-11-19 entries). All access was read-only; no forms, logins or writes.
Working files (PDFs, captions, probe results) are in `tmp/pbc/` (git-ignored, not committed).

## 1. Who served (Nov 2018 – Nov 2026)

Primary source: the "BCC COMMENTS – District N – COMMISSIONER …" block and cover page of the official BCC agenda PDFs
(`https://discover.pbc.gov/countycommissioners/Agenda_Master/YYYYMMDD.pdf`). I parsed 76 agendas (every Nov/Dec/Jan/Jun meeting, 2018–2026).
Seat changes happen at the November reorganization meeting, which the agenda labels "FINAL MEETING OF CURRENT BOARD"
(found on Nov 20 2018, Nov 17 2020, Nov 22 2022, Nov 19 2024, Nov 17 2026).

| District | Commissioner | Seat dates seen in the official record | Notes / source |
|---|---|---|---|
| 1 | Hal R. Valeche | in office at start of window → Nov 17, 2020 | agendas 2018-11-20 … 2020-06-16 |
| 1 | Maria G. Marino | Nov 17, 2020 → present | agendas 2020-11-17 … 2026-11-17; pbc.gov district list |
| 2 | Gregg K. Weiss | in office at start of window → Nov 17, 2026 | agendas 2018-11-20 … 2026-11-10; Nov 17 2026 cover lists him as outgoing board |
| 2 | Erica Whitfield | Nov 17, 2026 → present | Nov 17 2026 agenda (BCC comments: "District 2 – Commissioner Whitfield"); pbc.gov district list |
| 3 | Dave Kerner | in office at start of window → Jan 2023 (left for state job) | agendas through 2023-01-10; Palm Beach Post 2023-01-05 |
| 3 | Michael A. Barnett | sworn in Jan 10, 2023 (governor appointment) → Nov 19, 2024 | agendas 2023-01-24 … 2024-11-05; Palm Beach Post / WPTV 2023-01-11 |
| 3 | Joel G. Flores | Nov 19, 2024 → present | agendas 2024-11-19 … 2026-11-17 |
| 4 | Robert S. Weinroth | in office at start of window → Nov 22, 2022 | agendas through 2022-11-15 |
| 4 | Marci Woodward | Nov 22, 2022 → present (re-elected 2026 per Clerk remarks on Nov 17 2026 video) | agendas 2022-12-06 … 2026-11-17 |
| 5 | Mary Lou Berger | in office at start of window → Nov 17, 2020 | agendas 2018-11-20 … 2020-06-16 |
| 5 | Maria Sachs | Nov 17, 2020 → present | agendas 2020-11-17 … 2026-11-17 |
| 6 | Melissa McKinlay | in office at start of window → Nov 22, 2022 | agendas through 2022-11-15 |
| 6 | Sara Baxter | Nov 22, 2022 → Nov 17, 2026 | agendas 2022-12-06 … 2026-11-10 |
| 6 | Katherine M. Waldron | Nov 17, 2026 → present | Nov 17 2026 agenda; pbc.gov district list |
| 7 | Mack Bernard | in office at start of window → Nov 19, 2024 | agendas 2018-11-20 … 2024-11-05 |
| 7 | Bobby Powell Jr. | Nov 19, 2024 → present | agendas 2024-11-19 … 2026-11-17 |

Swearing-in dates = the reorganization meeting date where the agenda shows the board change. They are not yet checked
against Supervisor of Elections certifications or oath records; that check is a TODO before anything is published.

### Mayor / Vice Mayor (one-year terms, chosen at the November reorganization)

| Term (approx.) | Mayor | Vice Mayor | Evidence |
|---|---|---|---|
| Nov 2018 – Nov 2019 | Mack Bernard | Dave Kerner | Dec 2018 / Jan 2019 agendas label "MACK BERNARD, MAYOR", "DAVE KERNER, VICE MAYOR" |
| Nov 2019 – Nov 2020 | Dave Kerner | Robert Weinroth | Dec 2019 / Jan 2020 agenda text ("Mayor Kerner", "Vice Mayor Weinroth"), medium confidence |
| Nov 2020 – Nov 2021 | Dave Kerner | Robert Weinroth | Palm Beach Post 2020-11-17 ("By a 4-3 … keep Dave Kerner as mayor, Robert Weinroth as vice mayor"); June 2021 agenda |
| Nov 2021 – Nov 2022 | Robert Weinroth | Gregg Weiss | WPTV headline; Dec 2021 agenda text |
| Nov 2022 – Nov 2023 | Gregg Weiss | Maria Sachs | WPTV ("Gregg Weiss tapped as mayor, Maria Sachs becomes vice mayor") |
| Nov 2023 – Nov 2024 | Maria Sachs | Maria Marino | Palm Beach Post 2023-11-29; Jan 2024 agenda ("Vice Mayor Marino") |
| Nov 2024 – Nov 2025 | Maria Marino | Sara Baxter | County services guide "As of Nov. 19, 2024"; Clerk minutes excerpts ("Mayor Marino, Vice Mayor Baxter") |
| Nov 2025 – Nov 2026 | Sara Baxter | Marci Woodward | Nov 10 2026 agenda cover ("SARA BAXTER, Mayor", "MARCI WOODWARD, Vice Mayor") |
| Nov 17, 2026 – | Marci Woodward | Joel Flores | Nov 17 2026 meeting video (nomination and later congratulations); written record not out yet |

Wikipedia: no "Palm Beach County Board of County Commissioners" article exists (404), so there was nothing to cross-check there.

## 2. Where the record lives

| # | Source | Exact URL | Years | Format | Per-member votes? | Machine-readable / API | Blocks / limits hit |
|---|---|---|---|---|---|---|---|
| A | BCC agenda PDFs (order of business) | `https://discover.pbc.gov/countycommissioners/Agenda_Master/YYYYMMDD.pdf` (index: `https://discover.pbc.gov/countycommissioners/Pages/Agenda.aspx`, archive: `.../Pages/AgendaArchive.aspx`) | 2018 → now (all probed dates present) | PDF with a text layer | **No.** Items and motions only | Text extractable. The archive list is JavaScript-rendered and the SharePoint REST API returns 401, so I found dates by probing every Tuesday plus September weekdays | about 3% of HEADs timed out (000) and passed on retry. No 403s |
| B | BCC agenda HTML + item backup PDFs | `https://www.pbcgov.com/pubInf/Agenda/YYYYMMDD/YYYYMMDD.htm`; backups `.../YYYYMMDD/3B2.pdf` etc. | 2018 → now (checked 2018-12-04, 2022-12-06, 2026-11-10) | HTML + PDFs | **No** (agenda item summaries) | Yes: HTML links every backup PDF (~57–72 per meeting) | **https only**: `http://` returns HTTP 500. The directory listing is 403 |
| C | Clerk final minutes (official vote record) | Info page `https://www.mypalmbeachclerk.com/records/minutes`; research request form `.../records/minutes/board-services-research-request-form`; Board Services (561) 355-2951 | All years (the Clerk keeps them from 1909) | PDF | **Yes.** Each motion has "Motion by …, seconded by …, carried 6-1. Aye: … Nay: … Absent: …" | **No bulk online copy found.** The fee page lists "myMinutes online search – Free", but no working link exists (`/myminutes` redirects back to the Minutes page). Only the signature/last pages of approved minutes show up inside agenda backup 3B-2 | **Akamai 403** to plain curl on www.mypalmbeachclerk.com. A headless browser could read the pages |
| D | Minutes excerpts in agenda backup 3B-2 | e.g. `https://www.pbcgov.com/pubInf/Agenda/20260915/3B2.pdf`, `.../20251104/3B2.pdf` | Varies | Scanned + OCR PDF, 2–7 pages | Yes, but only for the few motions on the excerpted last pages | OCR text | Some meetings have no 3B-2 backup (Oct 6 2026 item says "available for inspection" only; Nov 10 2026 has no 3B2.pdf) |
| E | Meeting video: PBC TV YouTube | `https://www.youtube.com/@pbctvchannel20` (streams + videos) | BCC board meeting titles: 2023 (3), 2024 (12), 2025 (22), 2026 (49) (parts counted separately) | Video + auto-captions (VTT) | **Partly.** The chair announces the tally ("carries 6-1") and often names the dissenter. Unanimous votes have no names | Yes via yt-dlp (free): the caption file for a 6.5-hour meeting downloaded in ~2 s | None hit. Auto-captions garble names ("Saxs", "Pal") and item numbers ("51G" = 5E-1G) |
| F | County video library | `https://discover.pbc.gov/countycommissioners/Pages/BCC-Meeting-Videos.aspx` | 2015–2026 (counts below) | Video | Same as E | Grouped SharePoint list; I didn't resolve the item links (they need JS expansion) | None |
| G | BCC Briefs (county news posts) | `https://discover.pbc.gov/countycommissioners/Pages/Briefs.aspx` (e.g. Nov 10 2026 = `https://discover.pbc.gov/Lists/Newsroom/NewsDispForm.aspx?ID=7434`) | May 2023 → now (69 listed) | HTML | **No.** Regular-agenda outcomes only. The Nov 10 2026 brief doesn't mention its 6-1 vote | Scrapable HTML | None |
| H | Legistar API | `https://webapi.legistar.com/v1/pbc/` (public site `https://pbc.legistar.com`) | Sept 2025 – Apr 2026, **8 events only** | JSON API | The schema supports it (`/eventitems/{id}/votes` gives VotePersonName/VoteValueName) | **Yes, a public API exists** (client = `pbc`; `pbcgov`, `palmbeachcounty`, `pbcounty`, `palmbeach` → 500 "not set up") | **Test/training data, not the record**: items like "Appointment of new Head Mascot", "This is my sample item for testing", event comment "Kirsten's Test for Training". Not usable. Worth re-checking in case the County goes live |

The minutes backlog is real. The Oct 6 2026 consent item approved final minutes for June 14 2022, Sept 20 2022 and **Nov 15 2022**,
so official per-member votes for some meetings lag by up to ~4 years.

## 3. Volume estimate (Nov 2018 – Nov 2026)

- Agenda_Master PDFs found: **226** dates (223 on the first probe + 3 on retry); 219 confirmed on a second HEAD pass (6 were transient timeouts, plus 2026-09-23 is a 404).
  - Regular board meetings (PDF > 300 KB): **152 confirmed**, so ~155–160 including timeouts. That's ~19–20 per year (2019: 17, 2020: 18, 2021: 19, 2022: 20, 2023: 18, 2024: 19, 2025: 20, 2026 to date: 18; Nov–Dec 2018: 3).
  - Small agendas (workshops, budget hearings, specials): ~67.
  - Zoning and Comprehensive Plan hearings are separate (Planning/Zoning pages) and not counted. The county video library lists ~33–45 zoning/planning videos per year.
- County video library, all BCC categories: 2018: 99, 2019: 99, 2020: 91, 2021: 108, 2022: 98, 2023: 107, 2024: 101, 2025: 115, 2026: 85 videos. The "BCC Board Meetings" category is 28–38 per year because of AM/PM parts.
- Items per regular agenda (unique item codes in a 56-agenda sample): mean **65** (median 63, range 23–108), split as ~53 consent (3x), ~6 regular (5x) and ~4 public-hearing/other.
- **Total: ~10,000 agenda items over 8 years.** ~8,300 are consent items that normally pass in one 7-0 motion, so individually voted items are ~1,500–1,800, many with sub-motions. For example, 5E-1 on Nov 10 2026 was split into 36 separate votes, A–JJ.

## 4. Sample meeting end to end: Regular BCC meeting, Tuesday Nov 10, 2026

Sources pulled: agenda PDF (`Agenda_Master/20261110.pdf`, 86 pp, 83 item codes), HTML agenda (`pubInf/Agenda/20261110/20261110.htm`, 72 backup links),
BCC Brief (ID 7434), YouTube video `0Htit3BY3MY` "BCC Board Meeting - 11-10-2026" (6:35:01), auto-captions only.
Final Clerk minutes for Nov 10 2026 are not approved or published yet.

What could be extracted (captions):
- All 7 members voted early in the day (consent and agenda votes "carries 7-0"). Board: Mayor Baxter, Vice Mayor Woodward, Commissioners Flores, Marino, Powell, Sachs, Weiss.
- 17 motions announced 7-0 in the captions, including consent with pulled items 3H-2 to 3H-6 and 3I-7G, plus 5A/5B/5C items, with mover and seconder named each time (e.g. "motion by Vice Mayor Woodward, a second by Commissioner Marino").
- **Split vote: item 5E-1, "Reconsider and readopt the Convention Center hotel transaction and approve both hotel letter agreements"** (CityPlace South Tower II: $26,000,000 land purchase, 400-room Hotel 2, 33-year lease, etc.).
  The County Attorney asked for each sub-item to be voted separately. **36 separate motions (A through JJ). The captions have 35 announced "carries 6-1"; for one (5E-1GG, ~05:00:21) the caption has no tally.**
  The chair named the dissenter explicitly on the first several: "Please see the motion carry 6-1 showing that Commissioner Weiss was the dissenting vote" (04:52:28 into the video), and again at 04:53:11, 04:53:30 and 04:53:47.
  Later sub-items were announced as "6-1" without repeating the name. With all 7 present, the dissenter is presumably still Weiss, but that needs the minutes to confirm per item.
  Movers rotated among Marino, Powell, Woodward, Flores and Sachs. Weiss was recognized at 04:45:31, and his remarks end with "So, I will not be supporting that today" (~04:50:55).
- The BCC Brief for Nov 10 says only "approved to reconsider and readopt a purchase and sale agreement … $26,000,000". **No tally, no dissent.** So briefs alone would hide this split.

What could NOT be extracted:
- Official per-member Aye/Nay/Absent per item. That needs final minutes, which aren't online in bulk.
- Reliable names from captions without human review (caption errors: "Saxs" = Sachs, "Pal" = Powell, "51G" = 5E-1G).

Format of the official vote record (from minutes excerpts in `pubInf/Agenda/20251104/3B2.pdf` and `20260915/3B2.pdf`):

    MOTION to approve the request. Motion by Commissioner Powell, seconded by Commissioner Weiss, and carried 7-0.
    Aye: Mayor Marino, Vice Mayor Baxter, Commissioner Flores, Commissioner Powell, Commissioner Sachs, Commissioner Weiss, and Commissioner Woodward
    Nay: None
    Absent: None

This format is very easy to parse, once the minutes PDFs are in hand.

## 5. Recommendation

**Don't do a full 8-year per-vote ingest yet.** The official per-member record (Clerk final minutes) isn't online in bulk, and the only free online substitute (video captions) is reliable for split votes only after a human check.

Recommended phased plan:

1. **Phase 1, agenda index for all 8 years (cheap, fully official).** Ingest all ~226 Agenda_Master PDFs and the .htm agendas: meeting list, item codes, titles, departments and backup links.
   No votes, but it gives every meeting a page and makes items searchable.
   Runtime: ~75 MB per 76 agendas, so ~250 MB for 226. About 15–20 min of polite downloading (2 s spacing) plus parsing. ~1 working session.
2. **Phase 2, split votes and major items, 2023–2026, from video (unofficial until confirmed).** Pull captions for each YouTube board meeting (~85 titles).
   Auto-flag "carries N-M" with M>0, "fails", "dissent", "opposed" and named roll calls. A person verifies each flag against the video timestamp and the agenda item, and it's published as **"Reported at meeting (video, hh:mm:ss) – pending official minutes"**.
   Runtime: minutes to fetch, plus ~10–20 min of review per meeting with splits.
3. **Phase 3, official per-member votes, all years.** Get the final minutes PDFs from the Clerk. Either (a) find a working public myMinutes URL (I couldn't), or (b) Aaron files a public-records request with Board Services
   (boardservices@mypalmbeachclerk.com / 561-355-2951 / online form) for electronic copies of all BCC Regular, Budget and Zoning final minutes, Nov 2018 – present.
   I did **not** submit anything; that is Aaron's call. Once received, parse the Aye/Nay/Absent blocks (above) for complete per-member data, and use it to replace Phase 2 labels.
   Expected yield: every recorded motion, with Aye/Nay/Absent names (count per year unknown until the PDFs are in hand).
4. Pre-2023 video: the county library (source F) covers 2015–2026, but its link format needs a browser pass. Only worth doing if Phase 3 stalls.

Proposed site structure (static, GitHub Pages, no paid services):
- `/county/`: overview, current board, data sources and caveats.
- `/county/commissioners/<slug>/`: district, seat dates, mayor/vice-mayor years, list of their split votes (dissents and majorities), sources.
- `/county/meetings/YYYY-MM-DD/`: agenda summary, items, outcomes, votes (each vote tagged *official minutes* vs *video, unofficial*), links to PDFs and video timestamp.
- `/county/votes/split/`: sortable table of every non-unanimous vote.
- Data in `content/county/` (JSON/markdown), generated into `docs/county/`.

Risks:
- **Accuracy**: captions mis-hear names and numbers. Never publish a named vote from captions without a human check against the video, and label it unofficial.
- **Minutes lag**: official minutes can trail by years (2022 minutes approved Oct 2026).
- **Access**: www.mypalmbeachclerk.com returns Akamai 403 to scripts. pbcgov.com needs https (http gives 500). discover.pbc.gov has ~3% transient timeouts, so use retries and slow pacing.
- **Legistar trap**: the `pbc` Legistar API returns test/training data that looks real (names of sitting commissioners voting on "Head Mascot"). It must be excluded.
- **Consent agenda**: ~85% of items pass in one motion, so the "votes" are mostly identical 7-0s. Split votes are the newsworthy part.
- **Scope creep**: Zoning and Comp Plan hearings are separate bodies of records with their own agendas and minutes.
- **YouTube**: caption download via yt-dlp is free but depends on YouTube not blocking the box. It worked today.
