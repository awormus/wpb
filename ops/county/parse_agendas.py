#!/usr/bin/env python3
"""Parse Palm Beach County BCC agenda PDFs (+ HTML agendas for backup links) into content/county/meetings/*.json.
Inputs (git-ignored): tmp/pbc/ag/YYYYMMDD.pdf, tmp/pbc/htm/YYYYMMDD.htm. Read-only; no network."""
import re, json, os, subprocess, glob, html, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP = os.path.join(ROOT, 'tmp', 'pbc')
OUT = os.path.join(ROOT, 'content', 'county', 'meetings')
PDF_URL = 'https://discover.pbc.gov/countycommissioners/Agenda_Master/{k}.pdf'
HTM_URL = 'https://www.pbcgov.com/pubInf/Agenda/{k}/{k}.htm'
CODE = re.compile(r'^\s{0,12}(\d{1,2}[A-Z]{1,3}-\d{1,3})(?=\s|[A-Z*(])\s*[-–]?\s*(.*)$')
CODE_NODASH = re.compile(r'^\s{0,12}(\d{1,2}[A-Z]{1,2})\s+[-–]\s+(.+)$')   # e.g. "4A - Hunger and Homelessness ..."
DEPT = re.compile(r"^\s{0,12}([A-Z]{1,2})\.\s+([A-Z][A-Z0-9&,'’/().\- ]{2,})$")
PAGE = re.compile(r'^\s*Page\s+\d+\s*$')
SECTION_WORDS = [('CONSENT AGENDA', 'Consent'), ('REGULAR AGENDA', 'Regular'), ('PUBLIC HEARING', 'Public hearing'),
                 ('SPECIAL PRESENTATION', 'Special presentation'), ('BOARD APPOINTMENT', 'Board appointments'),
                 ('WORKSHOP', 'Workshop'), ('STAFF COMMENTS', 'Staff comments'), ('COMMISSIONER COMMENTS', 'Commissioner comments'),
                 ('BCC COMMENTS', 'Commissioner comments'), ('MATTERS BY THE PUBLIC', 'Public comment'), ('ADJOURNMENT', 'Adjournment')]
MONTHS = 'JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER'

def section_of(line):
    u = re.sub(r'\s+', ' ', line.strip().upper())
    if len(u) > 70 or re.search(r'[a-z]', line): return None
    for w, s in SECTION_WORDS:
        if w in u: return s
    return None

def pdf_text(f):
    return subprocess.run(['pdftotext', '-layout', f, '-'], capture_output=True, text=True).stdout

def clean(s):
    s = re.sub(r'\s+', ' ', s).strip()
    return s.replace('\u2019', "'")

def meeting_type(t, pages):
    ob = t.find('ORDER OF BUSINESS')
    head = re.sub(r'\s+', ' ', t[:6000] + (t[ob:ob + 3000] if ob > 0 else '')).upper()
    types = []
    full = re.sub(r'\s+', ' ', t).upper()
    if 'FINAL MEETING OF CURRENT BOARD' in head or 'ELECTION OF MAYOR' in full:
        types.append('Reorganizational meeting')
    if re.search(r'BUDGET PUBLIC HEARING|PUBLIC BUDGET HEARING|BUDGET HEARING', head): types.append('Budget public hearing')
    if re.search(r'\d\.\s*WORKSHOP', head) or 'WORKSHOP SESSION' in head: types.append('Workshop')
    if 'SPECIAL MEETING' in head: types.append('Special meeting')
    if 'ENVIRONMENTAL CONTROL' in head: types.append('Environmental Control Board session')
    if not [x for x in types if x != 'Environmental Control Board session'] or (pages and pages > 15 and 'Workshop' in types and 'CONSENT AGENDA' in head):
        types.insert(0, 'Regular board meeting')
    return '; '.join(dict.fromkeys(types))

def toc_items(t):
    lines = t.split('\n')
    try:
        start = next(i for i, l in enumerate(lines) if re.fullmatch(r'\s*TABLE\s+OF\s+CONTENTS\s*', l))
    except StopIteration:
        return []
    items, cur, section, dept, seen = [], None, None, None, set()
    for l in lines[start + 1:]:
        if re.match(r'^\s*\d+\.\s+(CONSENT AGENDA APPROVAL|CALL TO ORDER)', l) or re.match(r'^\s*\d+\.\s+CONSENT AGENDA\s*$', l):
            break
        if not l.strip() or PAGE.match(l) or re.match(rf'^\s*({MONTHS}) \d+, \d{{4}}\s*$', l) or re.match(r'^\s*\d{1,3}\s*$', l) or 'TABLE OF CONTENTS' in l:
            cur = None if not l.strip() else cur
            continue
        sec = section_of(l)
        m = CODE.match(l) or CODE_NODASH.match(l)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            cur = {'number': m.group(1), 'title': m.group(2).strip(), 'section': section, 'department': dept}
            items.append(cur); continue
        if sec and not m:
            section, dept, cur = sec, None, None; continue
        d = DEPT.match(l)
        if d and not m:
            dept, cur = clean(d.group(2)).title().replace('&Amp;', '&'), None; continue
        if cur is not None and l.startswith(' ') and len(l) - len(l.lstrip()) >= 8:
            cur['title'] += ' ' + l.strip()
    for it in items:
        it['title'] = clean(it['title'])
    return items

def outline_items(t):
    """Workshop/short agendas without a coded table of contents: take the lettered topics under numbered
    ORDER OF BUSINESS headings that are not procedural (call to order, agenda approval, adjournment)."""
    lines = t.split('\n'); items = []
    try:
        start = next(i for i, l in enumerate(lines) if 'ORDER OF BUSINESS' in l)
    except StopIteration:
        return []
    top, sec, cur = None, None, None
    for l in lines[start + 1:start + 120]:
        mt = re.match(r'^\s*(\d+)\s*\.\s+([A-Z][A-Z ,&/\-–()0-9.:]+?)\s*(\(Page.*)?$', l)
        if mt:
            if top and int(mt.group(1)) <= int(top) and items: break
            top, name = mt.group(1), mt.group(2).strip(); sec = section_of(name) or name.title(); cur = None
            continue
        ms = re.match(r'^\s{3,}([A-Z])[.)]\s+(.*)$', l)
        if ms and top and sec not in ('Adjournment', 'Staff comments', 'Commissioner comments', 'Regular', 'Consent') and not re.search(r'CALL TO ORDER|AGENDA APPROVAL', (sec or '').upper()):
            if ms.group(2).startswith('(Cont') or re.fullmatch(r'\d{1,2}:\d\d\s*[AP]\.?M\.?', ms.group(2).strip()): continue
            num = f'{top}.{ms.group(1)}'
            while any(i['number'] == num for i in items): num += "'"
            cur = {'number': num, 'title': clean(ms.group(2)), 'section': sec, 'department': None, 'numbering': 'from order of business'}
            items.append(cur); continue
        if cur is not None and re.match(r'^\s{12,}\S', l) and not re.match(r'^\s*\d+\s*\.', l):
            cur['title'] = clean(cur['title'] + ' ' + l)
        elif l.strip() == '':
            cur = None
    return items

def body_items(t):
    """Short special-meeting agendas with no table of contents and no lettered topics in the order of business:
    take numbered items from the agenda body, e.g. section 3 (REGULAR AGENDA), department A, item 1 -> 3A-1."""
    lines = t.split('\n')
    try:
        start = max(i for i, l in enumerate(lines) if 'ORDER OF BUSINESS' in l)
    except ValueError:
        return []
    items, top, sec, dept, cur = [], None, None, None, None
    for l in lines[start + 1:]:
        mt = re.match(r'^\s*(\d+)\.\s+([A-Z][A-Z ,&/\-()]+?)\s*$', l)
        if mt:
            top, sec, dept, cur = mt.group(1), section_of(mt.group(2)) or mt.group(2).title(), None, None; continue
        d = DEPT.match(l)
        if d and top:
            dept, cur = (d.group(1), clean(d.group(2)).title()), None; continue
        mi = re.match(r'^\s{3,}(\d{1,2})\.\s+(\S.*)$', l)
        if mi and top and dept and sec in ('Regular', 'Consent', 'Public hearing') and mi.group(2).strip()[:7].upper() != 'SUMMARY' \
                and not any(i['number'] == f'{top}{dept[0]}-{mi.group(1)}' for i in items) \
                and int(mi.group(1)) == 1 + sum(1 for i in items if i['number'].startswith(f'{top}{dept[0]}-')):
            cur = {'number': f'{top}{dept[0]}-{mi.group(1)}', 'title': mi.group(2).strip(), 'section': sec, 'department': dept[1],
                   'numbering': 'from agenda body'}
            items.append(cur); continue
        if mi: cur = None; continue
        if cur is not None:
            if re.search(r'SUMMARY', l) or len(cur['title']) > 400: cur = None; continue
            if l.strip(): cur['title'] += ' ' + l.strip()
    for it in items: it['title'] = clean(it['title'])
    return items

def backup_links(k):
    f = os.path.join(TMP, 'htm', f'{k}.htm')
    if not os.path.exists(f): return None
    s = open(f, 'rb').read().decode('cp1252', errors='ignore')
    links = []
    for h in re.findall(r'href=["\']?([^"\' >]+\.pdf)', s, re.I):
        h = html.unescape(h).replace('http://', 'https://')
        if not h.startswith('http'): h = f'https://www.pbcgov.com/pubInf/Agenda/{k}/' + h.lstrip('./')
        if h not in links: links.append(h)
    return links

def norm(code):
    return code.replace('-', '').replace('.', '').upper()

def build():
    os.makedirs(OUT, exist_ok=True)
    meetings = []
    for f in sorted(glob.glob(os.path.join(TMP, 'ag', '*.pdf'))):
        k = os.path.basename(f)[:8]
        date = f'{k[:4]}-{k[4:6]}-{k[6:]}'
        if not ('2018-11-01' <= date): continue
        t = pdf_text(f)
        info = subprocess.run(['pdfinfo', f], capture_output=True, text=True).stdout
        pages = int(re.search(r'Pages:\s+(\d+)', info).group(1)) if 'Pages:' in info else None
        items = toc_items(t); src = 'table of contents'
        if not items:
            items = outline_items(t); src = 'order of business' if items else None
        if pages and pages <= 10:
            extra = [i for i in body_items(t) if i['number'] not in {j['number'] for j in items}]
            if extra:
                items = items + extra; src = (src + ' + agenda body') if src else 'agenda body'
        links = backup_links(k)
        if links is not None:
            by = {}
            for u in links:
                stem = os.path.splitext(os.path.basename(u))[0].upper()
                by.setdefault(stem, []).append(u)
            for it in items:
                n = norm(it['number'])
                it['backup'] = [u for stem, us in by.items() for u in us if re.fullmatch(re.escape(n) + r'([A-Z]|[-_ ].*)?', stem)]
        rec = {
            'date': date,
            'type': meeting_type(t, pages),
            'agenda_pdf': PDF_URL.format(k=k),
            'agenda_html': HTM_URL.format(k=k) if links is not None else None,
            'agenda_pages': pages,
            'items_source': src,
            'item_count': len(items),
            'backup_pdf_count': len(links) if links is not None else None,
            'items': items,
            'source_note': 'Items and titles transcribed from the official agenda (table of contents or order of business). '
                           'Agendas list what was scheduled, not what was decided; votes are not in agendas.',
        }
        json.dump(rec, open(os.path.join(OUT, f'{date}.json'), 'w'), indent=1, ensure_ascii=False)
        meetings.append({k2: rec[k2] for k2 in ('date', 'type', 'agenda_pdf', 'agenda_html', 'agenda_pages', 'item_count', 'backup_pdf_count', 'items_source')})
    json.dump(meetings, open(os.path.join(ROOT, 'content', 'county', 'meetings.json'), 'w'), indent=1)
    return meetings

if __name__ == '__main__':
    ms = build()
    print(len(ms), 'meetings', sum(m['item_count'] for m in ms), 'items')
    for m in ms:
        if m['item_count'] == 0: print('NO ITEMS', m['date'], m['type'], m['agenda_pages'])
