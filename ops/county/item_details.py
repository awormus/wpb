#!/usr/bin/env python3
"""Read the body of each downloaded BCC agenda PDF (tmp/pbc/ag, git-ignored; no network) and add to
content/county/meetings/YYYY-MM-DD.json, per item:
  districts    - district tag printed at the end of the item ("District 2", "Districts 2, 3", "Countywide")
  named        - commissioners named in the item text with their title, e.g. "(Sponsored by Commissioner Berger)",
                 "Nominated by Mayor Weinroth", "(District 7)" is NOT a name and is only kept in districts.
                 Each entry: {surname, title, context} where context is sponsored | nominated | requested | named.
Also writes content/county/comments_roster.json: for each agenda, the district list printed in the
COMMISSIONER COMMENTS section ("District 2 – Commissioner Gregg K. Weiss")."""
import re, json, os, glob, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP = os.path.join(ROOT, 'tmp', 'pbc', 'ag'); OUT = os.path.join(ROOT, 'content', 'county')
SURN = ['Valeche', 'Marino', 'Weiss', 'Whitfield', 'Kerner', 'Barnett', 'Flores', 'Weinroth', 'Woodward', 'Berger',
        'Sachs', 'McKinlay', 'Baxter', 'Waldron', 'Bernard', 'Powell']
NAME = re.compile(r'\b(Commissioner|Comm\.|Vice[- ]Mayor|Mayor)\s+(?:(?:[A-Z][a-z]+|[A-Z]\.|Lou|G\.|K\.|S\.|A\.|R\.|M\.)\s+){0,3}?(' + '|'.join(SURN) + r')\b')
TOP = re.compile(r"^(\d{1,2}[A-Z]?)\.\s+([A-Z][A-Z &/,\-–’'()]+?)(?:\s*[-–]\s*\d.*|\s*\(CONT.*\))?\s*$")
DEPT = re.compile(r"^\s{2,10}([A-Z]{1,2})\.\s+([A-Z][A-Z0-9&,'’/().\- ]{2,}?)\s*(\(cont.*\))?\s*$", re.I)
ITEM = re.compile(r'^\s{5,14}(\d{1,2})\.\s+(\S.*)$')
LETTER = re.compile(r'^\s{3,10}([A-Z])\)\s+(\S.*)$')

def segments(text):
    lines = text.split('\n'); segs = {}; top = dept = None; cur = None; last = {}
    for l in lines:
        mt = TOP.match(l)
        if mt and '(PAGE' not in l.upper():
            t = mt.group(1)
            if t != top: dept = None
            top = t; cur = None; continue
        if top is None: continue
        md = DEPT.match(l)
        if md and not re.search(r'[a-z]{3}', md.group(2)):
            dept = md.group(1); cur = None; continue
        mi = ITEM.match(l)
        if mi:
            n = int(mi.group(1))
            key = (f'{top}-{n}' if re.fullmatch(r'\d+[A-Z]', top) else f'{top}{dept}-{n}') if (dept or re.fullmatch(r'\d+[A-Z]', top)) else None
            pref = key.rsplit('-', 1)[0] if key else None
            if key and n == last.get(pref, 0) + 1:
                last[pref] = n; cur = key; segs[cur] = mi.group(2) + ' '; continue
        ml = LETTER.match(l)
        if ml and dept is None and re.fullmatch(r'\d+', top):
            key = f'{top}{ml.group(1)}'
            if key not in segs: cur = key; segs[cur] = ml.group(2) + ' '; continue
        if cur and l.strip():
            if re.match(r'^\s*\*{5,}', l): cur = None; continue
            segs[cur] += l.strip() + ' '
    return segs

def districts(t):
    tail = t[-260:]
    out = set()
    for m in re.finditer(r'Districts?\s+((?:\d\s*(?:,|and|&|/|\s)\s*)*\d)\b', tail):
        out |= set(re.findall(r'\d', m.group(1)))
    out = sorted(d for d in out if d in '1234567')
    if re.search(r'Countywide', tail, re.I): out.append('Countywide')
    return out

def named(t):
    out = []
    for m in NAME.finditer(t):
        pre = t[max(0, m.start() - 40):m.start()]
        title = {'Comm.': 'Commissioner'}.get(m.group(1), m.group(1).replace('-', ' '))
        if re.search(r'Sponsored\s+by\s*$', pre, re.I): ctx = 'sponsored'
        elif re.search(r'(request(ed)?\s+(of|by)|at\s+the\s+request\s+of)\s*(the\s*)?$', pre, re.I): ctx = 'requested'
        elif re.search(r'NOMINATED|Nominated|Recommended\s+[Bb]y', t[max(0, m.start() - 400):m.start()]): ctx = 'nominated'
        else: ctx = 'named'
        e = {'surname': m.group(2), 'title': title, 'context': ctx}
        if e not in out: out.append(e)
    return out

def comments_roster(text):
    out = {}
    for m in re.finditer(r'District\s+(\d)\s*[–-]\s*(?:COMMISSIONER|Commissioner|MAYOR|Mayor|VICE MAYOR|Vice Mayor)\s+([A-Za-z .]+)', text):
        for s in SURN:
            if s.lower() in m.group(2).lower(): out[m.group(1)] = s
    return out

def main():
    roster = {}; stats = {'items': 0, 'with_districts': 0, 'with_named': 0}
    for f in sorted(glob.glob(os.path.join(TMP, '*.pdf'))):
        k = os.path.basename(f)[:8]; date = f'{k[:4]}-{k[4:6]}-{k[6:]}'
        jf = os.path.join(OUT, 'meetings', f'{date}.json')
        if not os.path.exists(jf): continue
        text = subprocess.run(['pdftotext', '-layout', f, '-'], capture_output=True, text=True).stdout
        roster[date] = comments_roster(text)
        segs = segments(text)
        m = json.load(open(jf))
        for it in m['items']:
            n = it['number']; key = n
            if re.fullmatch(r'\d+\.[A-Z]', n): key = n.replace('.', '')
            seg = segs.get(key)
            it.pop('districts', None); it.pop('named', None)
            stats['items'] += 1
            if not seg: continue
            seg = re.sub(r'\s+', ' ', seg)
            d = districts(seg); nm = named(seg)
            if d: it['districts'] = d; stats['with_districts'] += 1
            if nm: it['named'] = nm; stats['with_named'] += 1
        m['item_details_note'] = ('districts and named come from the item text in the agenda body (district tag at the end of '
                                  'each item; commissioners named with their title). Automated extraction; see the agenda PDF.')
        json.dump(m, open(jf, 'w'), indent=1, ensure_ascii=False)
    json.dump(roster, open(os.path.join(OUT, 'comments_roster.json'), 'w'), indent=1)
    print(stats)

if __name__ == '__main__':
    main()
