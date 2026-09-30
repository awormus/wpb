#!/usr/bin/env python3
"""Batch-convert last-12mo Commission agendas: ingest, summarize, publish docs.

Read-only external GETs only. Never stores binary PDFs.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import tempfile
import urllib.request
from datetime import date
from pathlib import Path

import markdown as mdlib

ROOT = Path("/home/box/wpb")
UA = "Mozilla/5.0 (compatible; WPBCivicBrief/1.0; +https://awormus.github.io/wpb/)"
RETRIEVED = date.today().isoformat()
QUEUE = ROOT / "ops/ingest-queue-12mo.json"
LOG = ROOT / "ops/external-access-log.md"
MEETINGS = ROOT / "content/meetings"
DOCS = ROOT / "docs/commission"

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def fetch_bytes(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, r.read()


def append_log(url: str, purpose: str, result: str) -> None:
    with LOG.open("a") as f:
        f.write(
            f"| {RETRIEVED} ET | Riley (WPB Data) | `{url}` | {purpose} | {result} |\n"
        )


def pretty_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{MONTHS[int(m) - 1]} {int(d)}, {y}"


def month_index_url(iso: str, kind: str) -> str:
    y, m, _ = iso.split("-")
    month = MONTHS[int(m) - 1]
    return (
        f"https://www.wpb.org/Our-City/City-Clerk/Commission-CRA-Agendas/"
        f"City-Commission-Agendas/City-Commission-Agendas-{y}/{y}-City-Commission-Agendas/"
        f"{month}-{y}"
    )


def ingest_one(row: dict) -> Path:
    iso = row["date"]
    pdf = row["pdf"]
    special = row["kind"] == "special"
    out_dir = MEETINGS / iso
    out_dir.mkdir(parents=True, exist_ok=True)
    out_md = out_dir / "agenda.md"

    status, data = fetch_bytes(pdf)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        pdf_path = Path(tf.name)
        tf.write(data)
    txt_path = Path(str(pdf_path) + ".txt")
    try:
        subprocess.run(
            ["pdftotext", str(pdf_path), str(txt_path)],
            check=True,
            capture_output=True,
        )
        title = (
            "Special City Commission Agenda"
            if special
            else "Final City Commission Agenda"
        )
        meeting = (
            "Special City Commission Meeting"
            if special
            else "Regular City Commission Meeting"
        )
        cmd = [
            "python3",
            str(ROOT / "ops/civic_pdf_cleanup.py"),
            str(txt_path),
            "--date",
            iso,
            "--doc-type",
            "agenda",
            "--title",
            title,
            "--meeting",
            meeting,
            "--official-pdf",
            pdf,
            "--retrieved",
            RETRIEVED,
            "--out",
            str(out_md),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        append_log(
            pdf,
            f"Ingest agenda {iso} (12mo batch)",
            f"Read-only GET; HTTP {status}; {len(data)} bytes; plain pdftotext; PDF deleted",
        )
    finally:
        pdf_path.unlink(missing_ok=True)
        txt_path.unlink(missing_ok=True)

    # orphan-dash QC
    body = out_md.read_text()
    orphans = sum(1 for line in body.splitlines() if line.strip() == "-")
    if orphans:
        raise RuntimeError(f"{iso}: {orphans} orphan lone '-' lines remain")
    return out_md


HEADING_RE = re.compile(
    r'^(#{2,3})\s+(\d{1,2}(?:\.\d{1,2}|\.[A-Za-z])?)\.\s+(.+?)(?:\s*<a id="(item-[^"]+)"></a>)?\s*$'
)
ANCHOR_ONLY_RE = re.compile(r'<a id="(item-[^"]+)"></a>')


def parse_items(agenda_text: str) -> list[dict]:
    """Extract ## / ### agenda item headings with anchors."""
    items = []
    for line in agenda_text.splitlines():
        m = HEADING_RE.match(line.strip())
        if not m:
            continue
        level = len(m.group(1))
        num = m.group(2)
        title = m.group(3).strip()
        title = re.sub(r"\s*<a id=\"[^\"]+\"></a>\s*", "", title).strip()
        anchor = m.group(4)
        if not anchor:
            # try reconstruct
            parts = num.lower().replace(".", "-")
            anchor = f"item-{parts}"
        items.append(
            {
                "level": level,
                "num": num,
                "title": title,
                "anchor": anchor,
                "parent": num.split(".")[0] if "." in num else num,
            }
        )
    return items


def section_bucket(title: str) -> str:
    t = title.upper()
    if "CONSENT" in t:
        return "consent"
    if "PROCLAMATION" in t or "PRESENTATION" in t or "AWARD" in t:
        return "ceremonial"
    if "PUBLIC HEARING" in t:
        return "hearing"
    if "RESOLUTION" in t and "ORDINANCE" not in t:
        return "resolutions"
    if "ORDINANCE" in t:
        return "ordinances"
    if "COMMENT" in t or "ADJOURN" in t or "CALL TO ORDER" in t:
        return "procedural"
    if "SPECIAL" in t or "BUDGET" in t or "MILLAGE" in t:
        return "special"
    return "other"


def write_summary(iso: str, pdf_url: str, kind: str) -> Path:
    agenda_path = MEETINGS / iso / "agenda.md"
    text = agenda_path.read_text()
    # frontmatter official_pdf if present
    m = re.search(r"^official_pdf:\s*(\S+)", text, re.M)
    if m:
        pdf_url = m.group(1)
    items = parse_items(text)
    special = kind == "special" or "Special" in (
        re.search(r"^meeting:\s*(.+)$", text, re.M).group(1)
        if re.search(r"^meeting:\s*(.+)$", text, re.M)
        else ""
    )
    meeting_title = (
        "Special City Commission Meeting"
        if special
        else "Regular City Commission Meeting"
    )
    pretty = pretty_date(iso)
    month_url = month_index_url(iso, kind)

    # group: top-level sections and their children
    tops = [i for i in items if i["level"] == 2]
    kids = [i for i in items if i["level"] == 3]
    by_parent: dict[str, list] = {}
    for k in kids:
        by_parent.setdefault(k["parent"], []).append(k)

    lines: list[str] = []
    lines.append("---")
    lines.append(f"date: {iso}")
    lines.append(f"title: {meeting_title}")
    lines.append(f"kind: {'special' if special else 'regular'}")
    lines.append('time: "17:00"')
    lines.append(
        'location: "Commission Chambers, 401 Clematis Street, West Palm Beach, FL 33401"'
    )
    lines.append("summary_basis: agenda")
    lines.append("agenda_text: ./agenda.md")
    lines.append(
        'notes: "Agenda-based summary only. Official minutes / pass-fail sheet not used for vote outcomes; do not treat items below as adopted outcomes."'
    )
    lines.append("sources:")
    lines.append(f"  - title: {('Special' if special else 'Final')} City Commission Agenda — {pretty}")
    lines.append(f"    url: {pdf_url}")
    lines.append(f"    retrieved: {RETRIEVED}")
    lines.append(f"  - title: {MONTHS[int(iso[5:7]) - 1]} {iso[:4]} City Commission Agendas (index)")
    lines.append(f"    url: {month_url}")
    lines.append(f"    retrieved: {RETRIEVED}")
    lines.append("  - title: Meetings & Agendas")
    lines.append("    url: https://www.wpb.org/Our-City/Meetings-Agendas")
    lines.append(f"    retrieved: {RETRIEVED}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {meeting_title} — {pretty}")
    lines.append("")
    lines.append(f"**When:** {pretty}, 5:00 PM  ")
    lines.append("**Where:** Commission Chambers, 401 Clematis Street  ")
    lines.append(
        "**Source:** Official agenda PDF on wpb.org (linked below). This page summarizes **what was scheduled**, not vote outcomes."
    )
    lines.append("")

    PROCEDURAL = {
        "CALL TO ORDER", "MOMENT OF SILENCE", "PLEDGE OF ALLEGIANCE",
        "CIVILITY AND DECORUM", "ADDITIONS / DELETIONS / REORGANIZATION OF AGENDA",
        "ADDITIONS/DELETIONS/REORGANIZATION OF AGENDA", "PUBLIC COMMENTS",
        "COMMENTS BY THE MAYOR AND CITY COMMISSIONERS", "ADJOURNMENT",
        "COMMENTS BY MAYOR AND CITY COMMISSIONERS",
    }

    def is_procedural(title: str) -> bool:
        u = " ".join(title.upper().split())
        if u in PROCEDURAL:
            return True
        if u.startswith("ADDITIONS") and "AGENDA" in u:
            return True
        if "PUBLIC COMMENT" in u:
            return True
        if u.startswith("ADJOURN"):
            return True
        return False

    if not tops and not kids:
        lines.append("_No numbered agenda item headings were detected in the extract; see the full text._")
        lines.append("")
    else:
        procedural_tops = [t for t in tops if is_procedural(t["title"])]
        substance = [t for t in tops if not is_procedural(t["title"])]
        if procedural_tops:
            lines.append("## Opening")
            lines.append("")
            lines.append(
                "Call to order, moment of silence, pledge, civility/decorum, and any agenda additions/deletions/reorganization (see full text for exact wording)."
            )
            lines.append("")
        for top in substance:
            bucket = section_bucket(top["title"])
            link = f"[{top['num']}](./agenda.md#{top['anchor']})"
            children = [c for c in kids if c["parent"] == top["num"]]

            heading_title = top["title"].title() if top["title"].isupper() else top["title"]
            lines.append(f"## {heading_title} ({link})")
            lines.append("")
            if children:
                for c in children:
                    ct = c["title"]
                    # shorten very long titles for summary list
                    short = ct if len(ct) <= 180 else ct[:177] + "…"
                    lines.append(
                        f"- **[{c['num']}](./agenda.md#{c['anchor']}):** {short}"
                    )
                lines.append("")
            else:
                lines.append(
                    f"See [{top['num']}. {heading_title}](./agenda.md#{top['anchor']}) in the full agenda text."
                )
                lines.append("")

        # orphan kids whose parent top missing
        covered_parents = {t["num"] for t in substance} if tops else set()
        orphans = [c for c in kids if c["parent"] not in covered_parents]
        if orphans:
            lines.append("## Other numbered items")
            lines.append("")
            for c in orphans:
                short = c["title"] if len(c["title"]) <= 180 else c["title"][:177] + "…"
                lines.append(
                    f"- **[{c['num']}](./agenda.md#{c['anchor']}):** {short}"
                )
            lines.append("")

    pf = MEETINGS / iso / "pass-fail.md"
    if pf.exists():
        lines.append("## Pass/fail sheet")
        lines.append("")
        lines.append(
            f"A normalized pass/fail extract is available at [`pass-fail.md`](./pass-fail.md). "
            "Use that file (and the official PDF) for recorded outcomes — this summary does not invent votes."
        )
        lines.append("")

    lines.append("## Official documents (on wpb.org — not stored here)")
    lines.append("")
    lines.append(f"- [Agenda PDF ({pretty})]({pdf_url})")
    lines.append(f"- [Month agendas folder]({month_url})")
    lines.append("")

    out = MEETINGS / iso / "summary.md"
    out.write_text("\n".join(lines))
    return out


SITE_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="stylesheet" href="../../styles.css">
</head>
<body>
  <header class="site-header">
    <div class="site-header-inner">
      <p class="site-title"><a href="../../">West Palm Beach Civic Brief</a></p>
      <p class="tagline">Public city data, commission summaries, and calendars — read-only, cited sources.</p>
      <nav class="site-nav" aria-label="Primary">
        <ul>
          <li><a href="../../">Home</a></li>
          <li><a href="../../demographics/">Demographics</a></li>
          <li><a href="../" aria-current="page">Commission</a></li>
          <li><a href="../../calendar/">Calendar</a></li>
          <li><a href="../../wiki/">Wiki</a></li>
          <li><a href="../../about/">About</a></li>
        </ul>
      </nav>
    </div>
  </header>
"""

SITE_FOOTER = """  <footer class="site-footer">
    <div class="site-footer-inner">
      <p>Maintained by Aaron’s WPB team. Sources are cited on each page.</p>
      <p>Last updated: {retrieved}.</p>
    </div>
  </footer>
</body>
</html>
"""


def strip_fm(text: str) -> str:
    if text.startswith("---"):
        m = re.match(r"^---\n.*?\n---\n?(.*)$", text, re.S)
        if m:
            return m.group(1)
    return text


def md_to_html_body(md: str) -> str:
    # Keep raw HTML anchors from cleanup
    return mdlib.markdown(
        md,
        extensions=["extra", "sane_lists", "nl2br"],
    )


def rewrite_summary_links_for_site(html_body: str) -> str:
    # ./agenda.md#item-x → agenda.html#item-x
    html_body = html_body.replace('href="./agenda.md#', 'href="agenda.html#')
    html_body = html_body.replace('href="./pass-fail.md"', 'href="https://github.com/awormus/wpb/blob/main/content/meetings/')
    # fix botched pass-fail - do simpler
    return html_body


def publish_docs(iso: str, pdf_url: str, kind: str) -> None:
    pretty = pretty_date(iso)
    special = kind == "special"
    out_dir = DOCS / iso
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_md = strip_fm((MEETINGS / iso / "summary.md").read_text())
    # site-relative links
    summary_md_site = summary_md.replace("](./agenda.md#", "](agenda.html#")
    summary_md_site = re.sub(
        r"\[`pass-fail\.md`\]\(\./pass-fail\.md\)",
        f"[`pass-fail.md`](https://github.com/awormus/wpb/blob/main/content/meetings/{iso}/pass-fail.md)",
        summary_md_site,
    )
    summary_html = md_to_html_body(summary_md_site)

    title = f"{pretty} City Commission — West Palm Beach Civic Brief"
    desc = (
        f"Agenda-based summary of the West Palm Beach City Commission meeting of {pretty}, "
        "with links into the full text extract and the official wpb.org PDF."
    )
    index = []
    index.append(SITE_HEADER.format(title=html.escape(title), desc=html.escape(desc)))
    index.append("  <main>")
    index.append('    <p class="note"><a href="../">← All commission summaries</a></p>')
    index.append(f"    <p class=\"note\"><a href=\"agenda.html\">Full agenda text →</a></p>")
    index.append(summary_html)
    index.append('    <section class="sources" aria-labelledby="sources-heading">')
    index.append('      <h2 id="sources-heading">On this site</h2>')
    index.append("      <ul>")
    index.append(f'        <li><a href="agenda.html">Full plain-text agenda extract</a></li>')
    index.append(
        f'        <li>Repo sources: <a href="https://github.com/awormus/wpb/blob/main/content/meetings/{iso}/summary.md"><code>summary.md</code></a>, '
        f'<a href="https://github.com/awormus/wpb/blob/main/content/meetings/{iso}/agenda.md"><code>agenda.md</code></a></li>'
    )
    index.append("      </ul>")
    index.append("    </section>")
    index.append("  </main>")
    index.append("")
    index.append(SITE_FOOTER.format(retrieved=RETRIEVED))
    (out_dir / "index.html").write_text("\n".join(index))

    # Full agenda text page
    agenda_raw = strip_fm((MEETINGS / iso / "agenda.md").read_text())
    agenda_html = md_to_html_body(agenda_raw)
    atitle = f"Agenda text — {pretty} — West Palm Beach Civic Brief"
    adesc = f"Full plain-text extract of the West Palm Beach City Commission agenda for {pretty}."
    a_parts = []
    a_parts.append(SITE_HEADER.format(title=html.escape(atitle), desc=html.escape(adesc)))
    a_parts.append("  <main>")
    a_parts.append(
        f'    <p class="note"><a href="./">← Summary</a> · <a href="../">All meetings</a></p>'
    )
    a_parts.append(f"    <h1>Full agenda text — {html.escape(pretty)}</h1>")
    a_parts.append(
        '    <p class="note">Plain-text extract for search and deep-linking. '
        f'The <a href="{html.escape(pdf_url)}">official PDF on wpb.org</a> is authoritative. Binary PDF is not hosted here.</p>'
    )
    a_parts.append(f'    <article class="agenda-extract">\n{agenda_html}\n    </article>')
    a_parts.append("  </main>")
    a_parts.append("")
    a_parts.append(SITE_FOOTER.format(retrieved=RETRIEVED))
    (out_dir / "agenda.html").write_text("\n".join(a_parts))


def blurb_from_summary(iso: str) -> str:
    p = MEETINGS / iso / "summary.md"
    text = strip_fm(p.read_text())
    # collect first few bold item lines
    bullets = re.findall(r"^- \*\*\[[^\]]+\]\([^)]+\):\*\* (.+)$", text, re.M)
    if not bullets:
        # fallback first ## after title
        heads = re.findall(r"^## (.+)$", text, re.M)
        heads = [h for h in heads if not h.startswith("Official")]
        if heads:
            return heads[0][:120]
        return "Agenda extract and summary."
    joined = "; ".join(b[:80] for b in bullets[:3])
    if len(joined) > 160:
        joined = joined[:157] + "…"
    return joined


def rebuild_index(rows: list[dict]) -> None:
    # Sort newest first
    rows_sorted = sorted(rows, key=lambda r: r["date"], reverse=True)
    cards = []
    for r in rows_sorted:
        iso = r["date"]
        pretty = pretty_date(iso)
        kind = "Special" if r["kind"] == "special" else "Regular"
        # try to refine special label from summary title line
        blurb = html.escape(blurb_from_summary(iso))
        cards.append(
            f"""      <li class="card">
        <h2><a href="{iso}/">{pretty} — {kind}</a></h2>
        <p>{blurb}</p>
      </li>"""
        )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Commission — West Palm Beach Civic Brief</title>
  <meta name="description" content="West Palm Beach City Commission meeting summaries and full agenda text extracts.">
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <header class="site-header">
    <div class="site-header-inner">
      <p class="site-title"><a href="../">West Palm Beach Civic Brief</a></p>
      <p class="tagline">Public city data, commission summaries, and calendars — read-only, cited sources.</p>
      <nav class="site-nav" aria-label="Primary">
        <ul>
          <li><a href="../">Home</a></li>
          <li><a href="../demographics/">Demographics</a></li>
          <li><a href="./" aria-current="page">Commission</a></li>
          <li><a href="../calendar/">Calendar</a></li>
          <li><a href="../wiki/">Wiki</a></li>
          <li><a href="../about/">About</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <main>
    <h1>City Commission</h1>
    <p>Agenda-based summaries and full plain-text extracts for the last 12 months of Commission meetings, linked to official PDFs on <a href="https://www.wpb.org/Our-City/Meetings-Agendas">wpb.org</a>. Summaries do not invent votes. Cross-topic pages: <a href="../wiki/">Wiki</a>.</p>
        <ul class="card-list" aria-label="Meeting summaries">
{chr(10).join(cards)}
    </ul>
  </main>

  <footer class="site-footer">
    <div class="site-footer-inner">
      <p>Maintained by Aaron’s WPB team. Sources are cited on each page.</p>
      <p>Last updated: {RETRIEVED} (12-month commission batch).</p>
    </div>
  </footer>
</body>
</html>
"""
    (DOCS / "index.html").write_text(page)


def main() -> None:
    rows = json.loads(QUEUE.read_text())
    # Prefer final over draft; queue already finals+specials
    errors = []
    for i, row in enumerate(rows, 1):
        iso = row["date"]
        print(f"[{i}/{len(rows)}] ingest {iso} …", flush=True)
        try:
            ingest_one(row)
            print(f"  summary {iso}", flush=True)
            write_summary(iso, row["pdf"], row["kind"])
            print(f"  publish {iso}", flush=True)
            publish_docs(iso, row["pdf"], row["kind"])
        except Exception as e:
            errors.append((iso, str(e)))
            print(f"  ERROR {iso}: {e}", flush=True)

    print("rebuild index", flush=True)
    # include all successfully present
    ok = [r for r in rows if (MEETINGS / r["date"] / "agenda.md").exists()]
    rebuild_index(ok)
    print(f"done. ok={len(ok)} errors={len(errors)}")
    for iso, err in errors:
        print(" ERR", iso, err)


if __name__ == "__main__":
    main()
