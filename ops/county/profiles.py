#!/usr/bin/env python3
"""Commissioner profiles: content/county/commissioners/<slug>.{json,md} and docs/county/commissioners/**.
Inputs (no network): roster_data.py, profile_data.py, content/county/meetings/*.json (with item_details.py fields),
content/county/comments_roster.json, tmp/pbc/prof/enr_bcc.json (parsed SOE results; summarized into the JSON output)."""
import json, os, re, glob, collections, datetime, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster_data import COMMISSIONERS, MAYORS, SOE, SOE_INDEX, REORG
from profile_data import PROFILES, ENR, ENR_URL, CHARTER, FLGOV, FLHSMV, PRE_TERMS
import build_site as B
E, fmt, page, write = B.E, B.fmt, B.page, B.write
ROOT = B.ROOT; CONTENT = B.CONTENT; DOCS = B.DOCS
CLERK_MIN = B.CLERK_MIN
SURNAME = {'hal-valeche': 'Valeche', 'maria-marino': 'Marino', 'gregg-weiss': 'Weiss', 'erica-whitfield': 'Whitfield',
           'dave-kerner': 'Kerner', 'michael-barnett': 'Barnett', 'joel-flores': 'Flores', 'robert-weinroth': 'Weinroth',
           'marci-woodward': 'Woodward', 'mary-lou-berger': 'Berger', 'maria-sachs': 'Sachs', 'melissa-mckinlay': 'McKinlay',
           'sara-baxter': 'Baxter', 'katherine-waldron': 'Waldron', 'mack-bernard': 'Bernard', 'bobby-powell-jr': 'Powell'}
END_FIX = {'2023-01': '2023-01-10'}   # Kerner: last agenda listing him; Barnett's oath was on the Jan 10, 2023 agenda
GH = 'https://github.com/awormus/wpb/blob/main/'
VOTES_NOTE = ('Per-member votes are not shown. How each commissioner voted is recorded only in the Clerk &amp; Comptroller’s final '
              'BCC minutes, which are not online in bulk; they are available by request from the Clerk’s Board Services '
              f'(561-355-2951, <a href="{CLERK_MIN}">mypalmbeachclerk.com/records/minutes</a>).')

def enr_url(eid):
    if eid in ENR_URL: return ENR_URL[eid]
    return SOE[ENR[eid][0]][1]

def elections_for(c, enr):
    sur = SURNAME[c['slug']]; out = []
    for eid, races in enr.items():
        for r in races:
            dm = re.search(r'(?:Commission|District)\s+(\d)', r['race'])
            if not dm or int(dm.group(1)) != c['district']: continue
            cands = [{'name': re.sub(r'\s+', ' ', x['name']).strip(), 'pct': x['pct'], 'votes': x['votes']} for x in r['candidates']]
            if not any(sur.lower() in x['name'].lower() for x in cands): continue
            top = max(cands, key=lambda x: int(x['votes'].replace(',', '')))
            me = next(x for x in cands if sur.lower() in x['name'].lower())
            key, label = ENR[eid]
            kind = 'primary' if key.endswith('P') else 'general'
            if len(cands) == 1: res = 'only candidate listed'
            else: res = ('won' if me is top else 'lost') + (' primary' if kind == 'primary' else '')
            out.append({'election': label, 'year': int(key[:4]), 'kind': kind, 'race': r['race'], 'result': res,
                        'candidate_as_listed': me['name'], 'votes': me['votes'], 'pct': me['pct'], 'total_votes': r['total'],
                        'all_candidates': cands, 'source': f'Palm Beach County Supervisor of Elections — {label}', 'url': enr_url(eid)})
    return sorted(out, key=lambda x: (x['year'], x['kind'] != 'primary'))

def window(c):
    s = c['start'] or '2018-11-01'; e = END_FIX.get(c['end'], c['end']) or '9999-12-31'
    return s, e

def main():
    enr = json.load(open(os.path.join(ROOT, 'tmp', 'pbc', 'prof', 'enr_bcc.json')))
    meetings = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(CONTENT, 'meetings', '*.json')))]
    croster = json.load(open(os.path.join(CONTENT, 'comments_roster.json')))
    os.makedirs(os.path.join(CONTENT, 'commissioners'), exist_ok=True)
    profiles = []
    for c in COMMISSIONERS:
        P = PROFILES[c['slug']]; sur = SURNAME[c['slug']]; s, e = window(c); D = str(c['district'])
        mine = [m for m in meetings if s <= m['date'] <= e]
        listed = [d for d, r in croster.items() if r.get(D) == sur]
        named = collections.defaultdict(list); dist_items = []; dist_specials = []; dist_sections = collections.Counter()
        for m in mine:
            for it in m['items']:
                ref = {'date': m['date'], 'number': it['number'], 'title': it['title'], 'section': it['section'],
                       'link': f'../../meetings/{m["date"]}/#item-{it["number"]}'}
                for n in it.get('named', []):
                    if n['surname'] == sur:
                        named[n['context']].append(dict(ref, as_title=n['title'])); break
                ds = it.get('districts') or []
                if D in ds:
                    if it['section'] == 'Special presentation': dist_specials.append(ref)
                    else:
                        dist_sections[it['section'] or 'Other'] += 1
                        if len([x for x in ds if x != 'Countywide']) == 1: dist_items.append(ref)
        terms = [m for m in MAYORS if c['slug'] in (m['mayor_slug'], m['vice_slug'])]
        el = elections_for(c, enr)
        party_code, party_key = P['party']
        party_src = next((x for x in el if x['election'].startswith(party_key[:4]) and (x['kind'][0].upper() == party_key[-1])), None)
        status = 'Serving' if not c['end'] else 'Left office'
        prof = {
            'slug': c['slug'], 'name': c['name'], 'district': c['district'],
            'seat': {'start': c['start'], 'start_note': c.get('start_note'), 'end': c['end'], 'end_note': c.get('end_note')},
            'took_seat': P['took_seat'],
            'party': {'code': party_code, 'source': party_src['source'] if party_src else None, 'url': party_src['url'] if party_src else None,
                      'note': 'Party as printed on Supervisor of Elections results (race label or candidate suffix).'},
            'status': status, 'left_office': [{'text': t, 'source': k} for t, k in (P['left'] or [])],
            'after_office': [{'text': t, 'source': k} for t, k in (P['next'] or [])],
            'mayor_terms': [{'term': m['term'], 'role': 'Mayor' if m['mayor_slug'] == c['slug'] else 'Vice Mayor', 'status': m['status'], 'evidence': m['evidence']} for m in terms],
            'elections': el, 'officer_term_ending_nov_2018': PRE_TERMS.get(c['slug']),
            'bio': [t for t, _ in P['bio']], 'bio_source': P['bio_src'](),
            'activity': {
                'window': {'from': s, 'to': None if e.startswith('9999') else e},
                'meetings_with_agenda': len(mine), 'first_meeting': mine[0]['date'] if mine else None, 'last_meeting': mine[-1]['date'] if mine else None,
                'agendas_listing_in_commissioner_comments': len(listed),
                'items_naming': {k: len(v) for k, v in named.items()},
                'items_naming_total': sum(len(v) for v in named.values()),
                'district_tagged_items': sum(dist_sections.values()), 'district_tagged_by_section': dict(dist_sections),
                'district_only_items': len(dist_items),
                'special_presentations_tagged_district': len(dist_specials),
                'named_items': {k: v for k, v in named.items()},
                'special_presentations': dist_specials,
            },
            'roster_status': c['status'], 'roster_evidence': c['evidence'],
            'sources_extra': {'charter': CHARTER, 'flgov': FLGOV, 'flhsmv': FLHSMV},
            'generated': B.TODAY,
        }
        json.dump(prof, open(os.path.join(CONTENT, 'commissioners', f'{c["slug"]}.json'), 'w'), indent=1, ensure_ascii=False)
        write_md(prof)
        profiles.append(prof)
        write(os.path.join(DOCS, 'commissioners', c['slug'], 'index.html'), render(prof))
    write(os.path.join(DOCS, 'commissioners', 'index.html'), render_index(profiles))
    print('profiles', len(profiles))
    for p in profiles:
        a = p['activity']
        print(f"{p['slug']:20} mtg={a['meetings_with_agenda']} listed={a['agendas_listing_in_commissioner_comments']} named={a['items_naming']} dist={a['district_tagged_items']} only={a['district_only_items']} sp={a['special_presentations_tagged_district']} el={len(p['elections'])}")

CTX = {'sponsored': 'as sponsor', 'requested': 'as requester', 'nominated': 'in a “Nominated by/Recommended by” list', 'named': 'other mentions'}
SRC = {'charter': CHARTER, 'flgov': FLGOV, 'flhsmv': FLHSMV}
def cite(key, p):
    if key == 'bio': s = p['bio_source']
    elif key == 'soe':
        x = p['elections'][-1] if p['elections'] else {'source': 'Supervisor of Elections results', 'url': SOE_INDEX}
        s = {'label': x['source'], 'url': x['url']}
    else: s = SRC[key]
    return f' <small>[<a href="{E(s["url"])}">{E(s["label"])}</a>]</small>'

def years(p):
    a = p['seat']['start'][:4] if p['seat']['start'] else 'before 2018'
    b = p['seat']['end'][:4] if p['seat']['end'] else 'present'
    return f'{a}–{b}'

def role_now(p):
    if p['seat']['end']: return 'Former commissioner'
    t = [m for m in p['mayor_terms'] if m['term'] == '2026–27']
    return t[0]['role'] if t else 'Commissioner'

def li_item(r, extra=''):
    return f'<li><a href="{E(r["link"])}">{E(fmt(r["date"]))}, item {E(r["number"])}</a>: {E(r["title"])}{extra}</li>'

def render(p):
    a = p['activity']; up = '../../'
    b = ['    <p class="note"><a href="../">← All commissioners</a> · <a href="../../">County home</a></p>',
         f'    <h1>{E(p["name"])} — District {p["district"]}</h1>',
         f'    <p class="lead">{E(role_now(p))}, Palm Beach County Board of County Commissioners. {E(p["status"])}.</p>',
         f'    <p class="note"><strong>Votes:</strong> {VOTES_NOTE}</p>',
         '    <h2>Basics</h2>', '    <ul>']
    seat = f'{fmt(p["seat"]["start"]) or "Before November 2018 (start of this record)"} – {fmt(p["seat"]["end"]) or "present"}'
    b.append(f'      <li><strong>District:</strong> {p["district"]}{cite("bio", p)}</li>')
    b.append(f'      <li><strong>Seat:</strong> {E(seat)}' + ''.join(f'<br><small>{E(n)}</small>' for n in (p['seat']['start_note'], p['seat']['end_note']) if n) +
             f' <small>[<a href="#sources">agendas and SOE results</a>]</small></li>')
    b.append(f'      <li><strong>How they took the seat:</strong> {E(p["took_seat"])}' + (cite('flgov', p) + cite('bio', p) if p['slug'] == 'michael-barnett' else cite('bio', p) if 'biography' in p['took_seat'] else (' <small>[<a href="#elections">SOE results</a>]</small>' if p['elections'] else cite('bio', p))) + '</li>')
    if p['party']['url']:
        b.append(f'      <li><strong>Party (as listed by the Supervisor of Elections):</strong> {E(p["party"]["code"])} <small>[<a href="{E(p["party"]["url"])}">{E(p["party"]["source"])}</a>]</small></li>')
    mt = '; '.join(f'{t["role"]} {t["term"]}' + ('' if t['status'] == 'verified' else f' ({t["status"]})') for t in p['mayor_terms']) or 'None between November 2018 and today'
    b.append(f'      <li><strong>Mayor / vice mayor (since Nov 2018):</strong> {E(mt)} <small>[<a href="#officers">evidence</a>]</small>' +
             (f'<br>Earlier: {E(p["officer_term_ending_nov_2018"]["text"])} <small>[{E(p["officer_term_ending_nov_2018"]["evidence"])}]</small>' if p.get('officer_term_ending_nov_2018') else '') + '</li>')
    b.append(f'      <li><strong>Status:</strong> {E(p["status"])}' + ''.join(f'<br>{E(x["text"])}{cite(x["source"], p)}' for x in p['left_office']) + '</li>')
    if p['after_office']:
        b.append('      <li><strong>After the Commission:</strong> ' + ''.join(f'{E(x["text"])}{cite(x["source"], p)}' for x in p['after_office']) + '</li>')
    b.append('    </ul>')
    # bio
    b += ['    <h2>Background</h2>', '    <ul>' + ''.join(f'<li>{E(t)}</li>' for t in p['bio']) + '</ul>',
          f'    <p><small>Source for this section: <a href="{E(p["bio_source"]["url"])}">{E(p["bio_source"]["label"])}</a>. Summarized in neutral terms; see the page for full text.</small></p>']
    # elections
    b.append('    <h2 id="elections">Elections</h2>')
    if p['elections']:
        b.append('    <table class="data"><thead><tr><th>Election</th><th>Race</th><th>Result</th><th>Candidates (votes, %)</th></tr></thead><tbody>')
        for x in p['elections']:
            cands = '<br>'.join(f'{E(c["name"])}: {E(c["votes"])} ({E(c["pct"])})' for c in x['all_candidates'])
            b.append(f'      <tr><td><a href="{E(x["url"])}">{E(x["election"])}</a></td><td>{E(x["race"])}</td><td>{E(x["result"])}, {E(x["pct"])}</td><td>{cands}</td></tr>')
        b.append('    </tbody></table>')
    b.append('    <p><small>Official results from the Palm Beach County Supervisor of Elections (enr.electionsfl.org, linked from '
             f'<a href="{SOE_INDEX}">votepalmbeach.gov Election Results</a>). Races decided without a contest do not appear on the results summaries.</small></p>')
    # officers
    b.append('    <h2 id="officers">Mayor and vice mayor terms</h2>')
    if p['mayor_terms']:
        b.append('    <ul>' + ''.join(f'<li><strong>{E(t["role"])}, {E(t["term"])}</strong> ({E(t["status"])}): {E("; ".join(t["evidence"]))}</li>' for t in p['mayor_terms']) + '</ul>')
    else:
        b.append('    <p>No mayor or vice mayor term between November 2018 and today in the agendas checked.</p>')
    # activity
    w = a['window']
    b += ['    <h2 id="agendas">On the agendas</h2>',
          f'    <p>From this site’s own data (official BCC agendas, {E(fmt(a["first_meeting"]))} – {E(fmt(a["last_meeting"]))}). '
          'Agendas show what was scheduled, not what was decided.</p>', '    <ul>',
          f'      <li><strong>{a["meetings_with_agenda"]}</strong> meetings with an official agenda during this tenure (the reorganizational meeting where a seat changes hands counts for both commissioners).</li>',
          f'      <li>Listed in the Commissioner Comments roster on <strong>{a["agendas_listing_in_commissioner_comments"]}</strong> agendas.</li>',
          f'      <li><strong>{a["items_naming_total"]}</strong> agenda items name them with their title in the item text: '
          + ', '.join(f'{v} {CTX[k]}' for k, v in sorted(a['items_naming'].items(), key=lambda kv: -kv[1])) + ('' if a['items_naming'] else 'none') + '.</li>',
          f'      <li><strong>{a["district_tagged_items"]}</strong> non-presentation items are tagged “District {p["district"]}” by County staff (alone or with other districts); '
          f'<strong>{a["district_only_items"]}</strong> name District {p["district"]} as the only district.</li>',
          f'      <li><strong>{a["special_presentations_tagged_district"]}</strong> special presentations (proclamations and recognitions) tagged District {p["district"]}.</li>',
          '    </ul>']
    ni = a['named_items']
    for k, label in (('sponsored', 'Items they sponsored (“Sponsored by …”)'), ('requested', 'Items described as requested by them'),
                     ('named', 'Other items that name them'), ('nominated', 'Advisory-board appointment items listing them under “Nominated by” / “Recommended by”')):
        if ni.get(k):
            rows = sorted(ni[k], key=lambda r: r['date'], reverse=True)
            lim = 25 if k in ('sponsored', 'requested') else 12
            b.append(f'    <h3>{E(label)} — {len(rows)}</h3>\n    <ul>' + ''.join(li_item(r) for r in rows[:lim]) + '</ul>' +
                     (f'<p><small>Showing {lim} most recent of {len(rows)}; full list in the <a href="{GH}content/county/commissioners/{p["slug"]}.json">JSON</a>.</small></p>' if len(rows) > lim else ''))
    if a['special_presentations']:
        rows = sorted(a['special_presentations'], key=lambda r: r['date'], reverse=True)
        b.append(f'    <h3>Special presentations tagged District {p["district"]} — {len(rows)}</h3>\n    <ul>' + ''.join(li_item(r) for r in rows[:15]) + '</ul>' +
                 (f'<p><small>Showing 15 most recent of {len(rows)}; full list in the <a href="{GH}content/county/commissioners/{p["slug"]}.json">JSON</a>.</small></p>' if len(rows) > 15 else ''))
    b.append('    <p><small>How these counts were made: item text comes from the agenda body; “District N” is the district tag County staff print at the end of each item; '
             'a commissioner is counted as named when the text uses their title and surname (e.g. “Sponsored by Commissioner Berger”, “Nominated by Mayor Weinroth”). '
             'This is automated extraction from the PDFs; follow the links to check an item. Script: '
             f'<a href="{GH}ops/county/item_details.py">ops/county/item_details.py</a>.</small></p>')
    b.append(f'    <p class="note">{VOTES_NOTE}</p>')
    # sources
    srcs = [f'<li>Biography: <a href="{E(p["bio_source"]["url"])}">{E(p["bio_source"]["label"])}</a></li>']
    srcs += [f'<li>{E(x["source"])}: <a href="{E(x["url"])}">{E(x["url"])}</a></li>' for x in {x['url']: x for x in p['elections']}.values()]
    srcs += [f'<li>{E(x)}</li>' for x in p['roster_evidence']]
    used = {x['source'] for x in p['left_office'] + p['after_office']} - {'soe', 'bio'}
    if p['slug'] == 'michael-barnett': used.add('flgov')
    srcs += [f'<li><a href="{E(SRC[k]["url"])}">{E(SRC[k]["label"])}</a></li>' for k in sorted(used)]
    srcs += [f'<li>Official BCC agendas: <a href="{B.AGENDA_PAGE}">{B.AGENDA_PAGE}</a></li>',
             f'<li>Structured data: <a href="{GH}content/county/commissioners/{p["slug"]}.json">content/county/commissioners/{p["slug"]}.json</a> · <a href="{GH}content/county/commissioners/{p["slug"]}.md">.md</a></li>',
             '<li>Photos are not included (no clearly public-domain official headshot was confirmed).</li>']
    b.append('    <section class="sources" id="sources"><h2>Sources</h2><ul>' + ''.join(srcs) + '</ul></section>')
    return page(3, f'{p["name"]}, District {p["district"]}', f'Profile of {p["name"]}, Palm Beach County Commission District {p["district"]}: seat, elections, background and agenda activity, with sources.', '\n'.join(b))

def render_index(profiles):
    rows = ''.join(f'<tr><td><a href="{p["slug"]}/">{E(p["name"])}</a></td><td>{p["district"]}</td><td>{E(years(p))}</td><td>{E(role_now(p))}' +
                   (f'<br><small>{E("; ".join(t["role"] + " " + t["term"] for t in p["mayor_terms"]))}</small>' if p['mayor_terms'] else '') + '</td></tr>'
                   for p in sorted(profiles, key=lambda p: (p['district'], p['seat']['start'] or '')))
    mrows = ''.join(f'<tr><td>{E(m["term"])}</td><td>{E(m["mayor"])}</td><td>{E(m["vice"])}</td><td>{E(m["status"])}</td></tr>' for m in MAYORS)
    b = ['    <p class="note"><a href="../">← County home</a></p>', '    <h1>Palm Beach County Commissioners, Nov 2018 – present</h1>',
         '    <p class="lead">Profiles of the 16 people who held a County Commission seat since November 2018: seat dates, elections, background from official County biography pages, and their footprint on the agendas.</p>',
         f'    <p class="note">{VOTES_NOTE}</p>',
         f'    <table class="data"><thead><tr><th>Name</th><th>District</th><th>Years</th><th>Role</th></tr></thead><tbody>{rows}</tbody></table>',
         '    <p><small>Years: seat start to end; “before 2018” means in office before this record begins (Nov 2018). Role: current title (County district pages, Nov 2026) or “Former commissioner”, with mayor/vice mayor terms since Nov 2018.</small></p>',
         '    <h2>Mayor and Vice Mayor</h2>', '    <p>The board picks a mayor and vice mayor for one-year terms at each November reorganizational meeting.</p>',
         f'    <table class="data"><thead><tr><th>Term</th><th>Mayor</th><th>Vice Mayor</th><th>Verification</th></tr></thead><tbody>{mrows}</tbody></table>',
         '    <section class="sources"><h2>Sources</h2><ul>'
         f'<li>Palm Beach County Supervisor of Elections, official results: <a href="{SOE_INDEX}">{SOE_INDEX}</a></li>'
         f'<li>Official BCC agendas: <a href="{B.AGENDA_PAGE}">{B.AGENDA_PAGE}</a></li>'
         '<li>Official County district Biography pages (discover.pbc.gov), current or archived on web.archive.org — linked on each profile.</li>'
         f'<li>Data: <a href="{GH}content/county/commissioners/">content/county/commissioners/</a> · <a href="{GH}content/county/commissioners.json">commissioners.json</a></li></ul></section>']
    return page(2, 'County Commissioners', 'Profiles of Palm Beach County commissioners since Nov 2018.', '\n'.join(b))

def write_md(p):
    a = p['activity']
    L = [f'# {p["name"]} — District {p["district"]}', '', f'_Generated {p["generated"]} from official sources; see links. Votes are not included (Clerk final minutes, by request: {CLERK_MIN})._', '',
         '## Basics', f'- Seat: {p["seat"]["start"] or "before 2018-11"} – {p["seat"]["end"] or "present"}', f'- Took seat: {p["took_seat"]}',
         f'- Party (SOE): {p["party"]["code"]} — {p["party"]["url"]}', f'- Status: {p["status"]}']
    L += [f'  - {x["text"]} [{x["source"]}]' for x in p['left_office'] + p['after_office']]
    L += [f'- {t["role"]} {t["term"]} ({t["status"]})' for t in p['mayor_terms']]
    L += ['', '## Background', *[f'- {t}' for t in p['bio']], f'- Source: {p["bio_source"]["label"]} — {p["bio_source"]["url"]}', '', '## Elections']
    for x in p['elections']:
        L.append(f'- {x["election"]} — {x["race"]}: {x["result"]}, {x["votes"]} votes ({x["pct"]}). Candidates: ' + '; '.join(f'{c["name"]} {c["votes"]} ({c["pct"]})' for c in x['all_candidates']) + f' — {x["url"]}')
    L += ['', '## On the agendas', f'- Meetings during tenure: {a["meetings_with_agenda"]}', f'- Commissioner Comments roster listings: {a["agendas_listing_in_commissioner_comments"]}',
          f'- Items naming them: {a["items_naming_total"]} {a["items_naming"]}', f'- District-tagged items: {a["district_tagged_items"]} (only this district: {a["district_only_items"]})',
          f'- Special presentations tagged their district: {a["special_presentations_tagged_district"]}']
    for k, rows in a['named_items'].items():
        L.append(f'### {k} ({len(rows)})')
        L += [f'- {r["date"]} {r["number"]}: {r["title"]}' for r in sorted(rows, key=lambda r: r['date'], reverse=True)]
    open(os.path.join(CONTENT, 'commissioners', f'{p["slug"]}.md'), 'w').write('\n'.join(L) + '\n')

if __name__ == '__main__':
    main()
