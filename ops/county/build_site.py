#!/usr/bin/env python3
"""Build content/county/commissioners.{json,md} and docs/county/** from content/county/meetings/*.json + roster_data.py.
No network. Run after parse_agendas.py."""
import json, os, glob, html, datetime, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster_data import COMMISSIONERS, MAYORS, SOE_INDEX, REORG
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONTENT = os.path.join(ROOT, 'content', 'county'); DOCS = os.path.join(ROOT, 'docs', 'county')
TODAY = datetime.date.today().isoformat()
E = html.escape
CLERK_MIN = 'https://www.mypalmbeachclerk.com/records/minutes'
AGENDA_PAGE = 'https://discover.pbc.gov/countycommissioners/Pages/Agenda.aspx'

def fmt(d):
    if not d: return ''
    if len(d) == 7: return datetime.date.fromisoformat(d + '-01').strftime('%B %Y')
    return datetime.date.fromisoformat(d).strftime('%B %-d, %Y')

def page(depth, title, desc, body, current='county'):
    up = '../' * depth
    nav = [('', 'Home'), ('demographics/', 'Demographics'), ('commission/', 'Commission'), ('county/', 'County'),
           ('calendar/', 'Calendar'), ('wiki/', 'Wiki'), ('about/', 'About')]
    navh = '\n'.join(f'          <li><a href="{up}{h}"' + (' aria-current="page"' if h == current + '/' else '') + f'>{t}</a></li>' for h, t in nav)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{E(title)} — West Palm Beach Civic Brief</title>
  <meta name="description" content="{E(desc)}">
  <link rel="stylesheet" href="{up}styles.css">
</head>
<body>
  <header class="site-header">
    <div class="site-header-inner">
      <p class="site-title"><a href="{up}">West Palm Beach Civic Brief</a></p>
      <p class="tagline">Public city data, commission summaries, and calendars — read-only, cited sources.</p>
      <nav class="site-nav" aria-label="Primary">
        <ul>
{navh}
        </ul>
      </nav>
    </div>
  </header>

  <main>
{body}
  </main>

  <footer class="site-footer">
    <div class="site-footer-inner">
      <p>Maintained by Aaron’s WPB team. Not an official Palm Beach County site. Sources are cited on each page.</p>
      <p>Last updated: {TODAY} (Palm Beach County BCC agenda ingest, Nov 2018 – Nov 2026).</p>
    </div>
  </footer>
</body>
</html>
'''

def scope_note(up):
    return (f'<p class="note"><strong>Scope:</strong> these pages list what was <em>scheduled</em> on official Palm Beach County '
            f'Board of County Commissioners agendas. They do not show how anyone voted. Official per-member votes are recorded only in the '
            f'Clerk &amp; Comptroller’s final minutes, which are not online in bulk; they are available by request from the Clerk’s '
            f'Board Services (561-355-2951, <a href="{CLERK_MIN}">mypalmbeachclerk.com/records/minutes</a>). '
            f'<a href="{up}">About this section →</a></p>')

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(text)

def board_on(date):
    out = []
    for c in COMMISSIONERS:
        s = c['start'] or '0000'; e = c['end'] or '9999'
        if len(e) == 7: e = e + '-31'
        if s <= date < e: out.append(c)
    return sorted(out, key=lambda c: c['district'])

def mayor_on(date, strict=False):
    cur = None
    for m in MAYORS:
        if m['start'] < date or (not strict and m['start'] == date): cur = m
    return cur

def officers(my):
    if not my: return ''
    s = f'Mayor {E(my["mayor"])}, Vice Mayor {E(my["vice"])}'
    if my['status'] != 'verified': s += f' ({E(my["status"])})'
    return s

def main():
    meetings = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(CONTENT, 'meetings', '*.json')))]
    # ---------- commissioners data ----------
    roster = []
    for c in COMMISSIONERS:
        terms = [m for m in MAYORS if c['slug'] in (m['mayor_slug'], m['vice_slug'])]
        rec = dict(c)
        rec['mayor_terms'] = [{'term': m['term'], 'role': 'Mayor' if m['mayor_slug'] == c['slug'] else 'Vice Mayor',
                               'verification': m['status'], 'evidence': m['evidence']} for m in terms]
        roster.append(rec)
    json.dump({'generated': TODAY, 'sources': {'soe_results_index': SOE_INDEX, 'agendas': AGENDA_PAGE},
               'reorganizational_meetings': REORG, 'commissioners': roster, 'mayors': MAYORS},
              open(os.path.join(CONTENT, 'commissioners.json'), 'w'), indent=1, ensure_ascii=False)
    md = ['# Palm Beach County Board of County Commissioners, Nov 2018 – present', '',
          f'Generated {TODAY} from `ops/county/roster_data.py`. Status: **verified** = seat dates backed by official agendas and Supervisor of Elections results; '
          '**verified-partial** = official agendas confirm service, but one date rests on press reports or falls outside this record.', '',
          '| District | Commissioner | Seat start | Seat end | Status |', '|---|---|---|---|---|']
    for c in sorted(roster, key=lambda c: (c['district'], c['start'] or '')):
        md.append(f"| {c['district']} | {c['name']} | {fmt(c['start']) or c.get('start_note','')} | {fmt(c['end']) or 'in office'} | {c['status']} |")
    md += ['', '## Mayor and Vice Mayor (one-year terms from each reorganizational meeting)', '',
           '| Term | Mayor | Vice Mayor | Status | Evidence |', '|---|---|---|---|---|']
    for m in MAYORS:
        md.append(f"| {m['term']} | {m['mayor']} | {m['vice']} | {m['status']} | {'; '.join(m['evidence'])} |")
    md += ['', f'Election results: Palm Beach County Supervisor of Elections ({SOE_INDEX}).']
    write(os.path.join(CONTENT, 'commissioners.md'), '\n'.join(md) + '\n')

    # ---------- meeting pages ----------
    by_year = collections.defaultdict(list)
    for m in meetings: by_year[m['date'][:4]].append(m)
    for m in meetings:
        d = m['date']; board = board_on(d); my = mayor_on(d, strict=True)
        new = next((x for x in MAYORS if x['start'] == d), None)
        secs = collections.OrderedDict()
        for it in m['items']: secs.setdefault(it['section'] or 'Other', []).append(it)
        b = [f'    <p class="note"><a href="../">← All County meetings</a> · <a href="../../">County home</a></p>',
             f'    <h1>Palm Beach County Commission — {fmt(d)}</h1>',
             f'    <p class="lead">{E(m["type"])}. {m["item_count"]} agenda items' + (f' (some numbered from the order of business or agenda body, not a table of contents)' if m['items_source'] != 'table of contents' else '') + '.</p>',
             '    ' + scope_note('../../'),
             f'    <p><strong>Official agenda:</strong> <a href="{E(m["agenda_pdf"])}">PDF ({m["agenda_pages"]} pages)</a>' +
             (f' · <a href="{E(m["agenda_html"])}">HTML agenda with item backup PDFs</a>' if m['agenda_html'] else ' · HTML agenda not available') + '</p>']
        if board:
            names = ', '.join(f'<a href="../../commissioners/{c["slug"]}/">{E(c["name"])}</a> (D{c["district"]})' for c in board)
            b.append(f'    <p><strong>Board on this date (from the roster, not from attendance records):</strong> {names}.' +
                     (f' Presiding officers going into this meeting: {officers(my)}.' if my else '') +
                     (f' This reorganizational meeting chose {officers(new)}.' if new else '') + '</p>')
        if not m['items']:
            b.append('    <p class="empty-state">No agenda items could be read from this agenda. See the official PDF.</p>')
        for sec, its in secs.items():
            b.append(f'    <h2>{E(sec)} ({len(its)})</h2>\n    <ul>')
            dept = None
            for it in its:
                bl = ''.join(f' <a href="{E(u)}">[backup{"" if len(it.get("backup",[]))==1 else " "+str(i+1)}]</a>' for i, u in enumerate(it.get('backup', [])))
                dp = f' <em>({E(it["department"])})</em>' if it.get('department') else ''
                b.append(f'      <li id="item-{E(it["number"])}"><strong>{E(it["number"])}</strong>{dp}: {E(it["title"])}{bl}</li>')
            b.append('    </ul>')
        b.append(f'''    <section class="sources">
      <h2>Sources</h2>
      <ul>
        <li>Palm Beach County BCC agenda, {fmt(d)}: <a href="{E(m["agenda_pdf"])}">{E(m["agenda_pdf"])}</a></li>
''' + (f'        <li>HTML agenda (links each item’s backup PDF): <a href="{E(m["agenda_html"])}">{E(m["agenda_html"])}</a></li>\n' if m['agenda_html'] else '') +
f'''        <li>Agenda index: <a href="{AGENDA_PAGE}">discover.pbc.gov BCC Meeting Agendas</a></li>
        <li>Item titles are transcribed from the agenda’s {E(m['items_source'] or 'table of contents')}; long titles are as printed. Agendas can change at the meeting (see the agenda’s additions/deletions sheet).</li>
        <li>Structured data: <a href="https://github.com/awormus/wpb/blob/main/content/county/meetings/{d}.json">content/county/meetings/{d}.json</a></li>
      </ul>
    </section>''')
        write(os.path.join(DOCS, 'meetings', d, 'index.html'),
              page(3, f'County Commission {fmt(d)}', f'Agenda items for the Palm Beach County Board of County Commissioners meeting of {fmt(d)}.', '\n'.join(b)))

    # meetings index
    b = ['    <p class="note"><a href="../">← County home</a></p>', '    <h1>Palm Beach County Commission meetings, Nov 2018 – present</h1>',
         f'    <p class="lead">{len(meetings)} meetings with an official agenda on discover.pbc.gov, {sum(m["item_count"] for m in meetings):,} agenda items.</p>',
         '    ' + scope_note('../')]
    for y in sorted(by_year, reverse=True):
        b.append(f'    <h2>{y} ({len(by_year[y])})</h2>\n    <ul>')
        for m in sorted(by_year[y], key=lambda m: m['date'], reverse=True):
            b.append(f'      <li><a href="{m["date"]}/">{fmt(m["date"])}</a> — {E(m["type"])}, {m["item_count"]} items</li>')
        b.append('    </ul>')
    b.append(f'    <section class="sources"><h2>Sources</h2><ul><li>Official agendas: <a href="{AGENDA_PAGE}">discover.pbc.gov BCC Meeting Agendas</a> (PDFs at discover.pbc.gov/countycommissioners/Agenda_Master/YYYYMMDD.pdf; HTML agendas at www.pbcgov.com/pubInf/Agenda/YYYYMMDD/YYYYMMDD.htm).</li></ul></section>')
    write(os.path.join(DOCS, 'meetings', 'index.html'), page(2, 'County Commission meetings', 'All Palm Beach County BCC meetings with official agendas since Nov 2018.', '\n'.join(b)))

    # ---------- commissioner pages ----------
    for c in roster:
        mine = [m for m in meetings if c in [x for x in board_on(m['date'])] or any(x['slug'] == c['slug'] for x in board_on(m['date']))]
        stat = {'verified': 'Verified against official agendas and Supervisor of Elections results.',
                'verified-partial': 'Partly verified: official agendas confirm service; see notes for anything that rests on press reports or falls outside this record.'}[c['status']]
        b = ['    <p class="note"><a href="../">← All commissioners</a> · <a href="../../">County home</a></p>',
             f'    <h1>{E(c["name"])} — District {c["district"]}</h1>',
             f'    <p class="lead">Seat: {E(fmt(c["start"]) or "before November 2018")} – {E(fmt(c["end"]) or "present")}.</p>',
             f'    <p><strong>Verification:</strong> {E(stat)}</p>']
        notes = [c.get('start_note'), c.get('end_note')]
        b.append('    <ul>' + ''.join(f'<li>{E(n)}</li>' for n in notes if n) + '</ul>')
        b.append('    <h2>Mayor / Vice Mayor</h2>')
        if c['mayor_terms']:
            b.append('    <ul>' + ''.join(f'<li>{E(t["role"])}, {E(t["term"])} — {E(t["verification"])} ({E("; ".join(t["evidence"]))})</li>' for t in c['mayor_terms']) + '</ul>')
        else:
            b.append('    <p>No mayor or vice mayor term between November 2018 and today.</p>')
        b.append('    <h2>Elections in this record (Supervisor of Elections)</h2>')
        if c['elections']:
            b.append('    <ul>' + ''.join(f'<li>{E(x["source"])} — {E(x["race"])}: {E(x["result"])} (<a href="{E(x["url"])}">results</a>)</li>' for x in c['elections']) + '</ul>')
        else:
            b.append('    <p>Not on a County Commission ballot between 2018 and 2026 in the SOE results checked.</p>')
        b.append(f'    <h2>Meetings during this tenure ({len(mine)})</h2>')
        b.append('    <p>Votes are not shown: official per-member votes are in the Clerk’s final minutes, which are not online in bulk. '
                 'Meetings with an official agenda while this commissioner held the seat:</p>')
        yrs = collections.OrderedDict()
        for m in mine: yrs.setdefault(m['date'][:4], []).append(m)
        b.append('    <ul>' + ''.join(f'<li>{y}: ' + ', '.join(f'<a href="../../meetings/{m["date"]}/">{datetime.date.fromisoformat(m["date"]).strftime("%b %-d")}</a>' for m in ms) + '</li>' for y, ms in yrs.items()) + '</ul>')
        b.append('    <section class="sources"><h2>Sources</h2><ul>' + ''.join(f'<li>{E(x)}</li>' for x in c['evidence']) +
                 f'<li>Supervisor of Elections results index: <a href="{SOE_INDEX}">{SOE_INDEX}</a></li>'
                 f'<li>Official BCC agendas: <a href="{AGENDA_PAGE}">{AGENDA_PAGE}</a></li>'
                 '<li>Structured data: <a href="https://github.com/awormus/wpb/blob/main/content/county/commissioners.json">content/county/commissioners.json</a></li></ul></section>')
        write(os.path.join(DOCS, 'commissioners', c['slug'], 'index.html'),
              page(3, f'{c["name"]}, District {c["district"]}', f'{c["name"]}, Palm Beach County Commission District {c["district"]}: seat dates, mayor years, and sources.', '\n'.join(b)))

    # commissioners index
    rows = ''.join(f'<tr><td>{c["district"]}</td><td><a href="{c["slug"]}/">{E(c["name"])}</a></td><td>{E(fmt(c["start"]) or "before Nov 2018")}</td><td>{E(fmt(c["end"]) or "in office")}</td><td>{E(c["status"])}</td></tr>'
                   for c in sorted(roster, key=lambda c: (c['district'], c['start'] or '')))
    mrows = ''.join(f'<tr><td>{E(m["term"])}</td><td>{E(m["mayor"])}</td><td>{E(m["vice"])}</td><td>{E(m["status"])}</td></tr>' for m in MAYORS)
    b = ['    <p class="note"><a href="../">← County home</a></p>', '    <h1>Palm Beach County Commissioners, Nov 2018 – present</h1>',
         '    <p class="lead">Seven single-member districts. Seat dates come from official BCC agendas and Supervisor of Elections results; new terms start at the reorganizational meeting after each general election.</p>',
         f'    <table class="data"><thead><tr><th>District</th><th>Commissioner</th><th>Seat start</th><th>Seat end</th><th>Verification</th></tr></thead><tbody>{rows}</tbody></table>',
         '    <h2>Mayor and Vice Mayor</h2>', '    <p>The board picks a mayor and vice mayor for one-year terms at each November reorganizational meeting.</p>',
         f'    <table class="data"><thead><tr><th>Term</th><th>Mayor</th><th>Vice Mayor</th><th>Verification</th></tr></thead><tbody>{mrows}</tbody></table>',
         '    <section class="sources"><h2>Sources</h2><ul>'
         f'<li>Palm Beach County Supervisor of Elections, official results: <a href="{SOE_INDEX}">{SOE_INDEX}</a> (race-by-race links on each commissioner page)</li>'
         f'<li>Official BCC agendas (district roster in the BCC comments section; mayor/vice mayor in item sponsorships and cover pages): <a href="{AGENDA_PAGE}">{AGENDA_PAGE}</a></li>'
         '<li>Press reports are used only where noted, and those entries are marked partial or pending.</li>'
         '<li>Data: <a href="https://github.com/awormus/wpb/blob/main/content/county/commissioners.json">commissioners.json</a> · <a href="https://github.com/awormus/wpb/blob/main/content/county/commissioners.md">commissioners.md</a></li></ul></section>']
    write(os.path.join(DOCS, 'commissioners', 'index.html'), page(2, 'County Commissioners', 'Palm Beach County commissioners since Nov 2018: seat dates and mayors.', '\n'.join(b)))

    # ---------- county index ----------
    cur = board_on(TODAY); my = mayor_on(TODAY)
    cards = ''.join(f'<li><a href="commissioners/{c["slug"]}/">{E(c["name"])}</a>, District {c["district"]}</li>' for c in cur)
    nyears = {y: len(v) for y, v in sorted(by_year.items())}
    ylist = ', '.join(f'{y}: {n}' for y, n in nyears.items())
    b = ['    <h1>Palm Beach County Commission</h1>',
         '    <p class="lead">Agendas of the Palm Beach County Board of County Commissioners (BCC) since November 2018, plus who held each seat. '
         'West Palm Beach is the county seat, and many County decisions (Convention Center, roads, transit, housing money) land in the city.</p>',
         '    <h2>What these pages are — and are not</h2>',
         '    <ul>',
         '      <li><strong>Agenda items only.</strong> Each meeting page lists what was scheduled on the official agenda, with links to the County’s agenda PDF, HTML agenda and item backup PDFs. Agendas do not record outcomes or votes.</li>',
         f'      <li><strong>No per-member votes.</strong> How each commissioner voted is recorded only in the Clerk &amp; Comptroller’s final BCC minutes. Those are not online in bulk: they are available only by request from the Clerk’s Board Services, 561-355-2951 (<a href="{CLERK_MIN}">mypalmbeachclerk.com/records/minutes</a>). The Clerk’s former “myMinutes” online search is no longer available.</li>',
         '      <li><strong>Not included:</strong> BCC zoning and comprehensive-plan hearings (separate agendas from Planning, Zoning &amp; Building), meeting video, and County advisory boards.</li>',
         '      <li>This is not an official County site. Everything here was read from public County and Supervisor of Elections pages, read-only.</li>',
         '    </ul>',
         f'    <p><strong>Current board</strong> (from {fmt(REORG[2026])}' + (f'; {officers(my)}' if my else '') + f'):</p>\n    <ul>{cards}</ul>',
         '    <ul class="card-list">',
         f'      <li class="card"><h2><a href="meetings/">Meetings</a></h2><p>{len(meetings)} meetings with official agendas, {sum(m["item_count"] for m in meetings):,} agenda items. By year — {ylist}.</p></li>',
         f'      <li class="card"><h2><a href="commissioners/">Commissioners</a></h2><p>{len(roster)} people who held a seat since Nov 2018: seat dates, mayor and vice mayor years, checked against Supervisor of Elections results and County agendas.</p></li>',
         '    </ul>',
         '    <section class="sources"><h2>Sources</h2><ul>',
         f'      <li>BCC agendas: <a href="{AGENDA_PAGE}">{AGENDA_PAGE}</a> — PDFs at <code>discover.pbc.gov/countycommissioners/Agenda_Master/YYYYMMDD.pdf</code>; HTML agendas at <code>www.pbcgov.com/pubInf/Agenda/YYYYMMDD/YYYYMMDD.htm</code></li>',
         f'      <li>Final minutes (official votes): Clerk &amp; Comptroller Board Services, by request — <a href="{CLERK_MIN}">{CLERK_MIN}</a>, 561-355-2951</li>',
         f'      <li>Election results: <a href="{SOE_INDEX}">Palm Beach County Supervisor of Elections</a></li>',
         '      <li>How this was built: <a href="https://github.com/awormus/wpb/tree/main/ops/county">ops/county/</a>; every fetch is logged in <a href="https://github.com/awormus/wpb/blob/main/ops/external-access-log.md">ops/external-access-log.md</a></li>',
         '    </ul></section>']
    write(os.path.join(DOCS, 'index.html'), page(1, 'Palm Beach County Commission', 'Palm Beach County BCC agendas since Nov 2018 and commissioner roster, with sources and limits.', '\n'.join(b)))
    print('built', len(meetings), 'meetings', len(roster), 'commissioners')
    import profiles; profiles.main()   # full commissioner profiles overwrite the basic commissioner pages

if __name__ == '__main__':
    main()
