#!/usr/bin/env python3
"""Civic PDF extract → normalized markdown with stable item-* anchors.

Reads existing agenda/pass-fail markdown (or raw pdftotext), applies the
civic-pdf-to-markdown cleanup standard, and writes normalized .md.

Usage:
  python3 ops/civic_pdf_cleanup.py path/to/agenda.md
  python3 ops/civic_pdf_cleanup.py path/to/extract.txt --date 2026-08-03 \\
      --doc-type agenda --title "..." --meeting "..." --official-pdf URL \\
      --retrieved 2026-09-30 --out path/to/agenda.md

Never stores binary PDFs. Prefers plain pdftotext (no -layout). Flattens to a single left-aligned column. Structural cleanup only — no invented facts.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

EXTRACTOR = "pdftotext + civic-pdf-cleanup"

BULLET_RE = re.compile(r"[•●▪◦‣]")
PAGE_ONLY_RE = re.compile(r"^\s*Page\s+\d+(?:\s+of\s+\d+)?\s*$", re.I)
# Trailing "Page N of M" on an otherwise empty-ish line (common in pdftotext -layout)
PAGE_TRAIL_RE = re.compile(r"^[ \t]*Page\s+\d+(?:\s+of\s+\d+)?[ \t]*$")

# Running header fragments (keep first cluster; strip later repeats)
CITY_LINE_RE = re.compile(r"^\s*City of West Palm Beach\s*$", re.I)
AGENDA_HDR_RE = re.compile(
    r"^\s*(?:Special\s+)?City\s+Commission(?:\s+Agenda|\s+Pass/?Fail(?:\s+Agenda)?)?\s*$",
    re.I,
)
PASSFAIL_HDR_RE = re.compile(r"^\s*Pass/?Fail\s+Agenda\s*$", re.I)
AGENDA_WORD_RE = re.compile(r"^\s*Agenda\s*$", re.I)
DATE_HDR_RE = re.compile(
    r"^\s*(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+)?"
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},\s+\d{4}\s*$",
    re.I,
)
PUBLIC_HEARING_HDR_RE = re.compile(r"^\s*Public Hearing\b.*$", re.I)
TIME_HDR_RE = re.compile(r"^\s*\d{1,2}:\d{2}\s*(?:AM|PM)\s*$", re.I)

# Agenda item lines
# Sub-item: 7.1. Title   or  10.1. Title (optional trailing period after major)
SUB_ITEM_RE = re.compile(
    r"^(\s{0,10})(\d{1,2})\.(\d{1,2})\.(\s+)(.+)$"
)
# Letter part: 12.A. Title
LETTER_ITEM_RE = re.compile(
    r"^(\s{0,10})(\d{1,2})\.([A-Za-z])\.(\s+)(.+)$"
)
# Top-level: 7.   CONSENT CALENDAR  (light indent; not a year)
TOP_ITEM_RE = re.compile(
    r"^(\s{0,4})(\d{1,2})\.(\s+)(.+)$"
)

# Body numbered lists to avoid (deep indent, single digit period without sub)
FIELD_LABELS = {
    "originating department:",
    "ordinance/resolution:",
    "background information:",
    "fiscal impact:",
    "recommended action:",
}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (flat string-valued frontmatter dict best-effort, body)."""
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), m.group(2)
    meta: dict[str, str] = {}
    # Simple key: value lines; ignore folded blocks beyond first line marker
    current_key = None
    folded = False
    for line in fm_raw.splitlines():
        if folded:
            if line.startswith("  ") or line.startswith("\t"):
                continue
            folded = False
            current_key = None
        km = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if km:
            key, val = km.group(1), km.group(2)
            if val in (">", "|", ">-", ">-"):
                folded = True
                current_key = key
                meta[key] = ""
            else:
                meta[key] = val.strip().strip("'\"")
                current_key = key
        # skip list items etc.
    return meta, body


def extract_raw_body(body: str) -> str:
    """Drop existing H1 / PDF link / disclaimer wrapper; keep extract."""
    lines = body.splitlines()
    # Prefer content after standalone HR
    hr_idxs = [i for i, ln in enumerate(lines) if ln.strip() == "---"]
    if hr_idxs:
        return "\n".join(lines[hr_idxs[0] + 1 :])
    # Else skip leading markdown headings/links until address or item
    start = 0
    for i, ln in enumerate(lines):
        if ln.startswith("401 Clematis") or TOP_ITEM_RE.match(ln) or SUB_ITEM_RE.match(ln):
            start = i
            break
        if CITY_LINE_RE.match(ln.strip()):
            start = i
            break
    return "\n".join(lines[start:])


def drop_formfeeds(text: str) -> str:
    return text.replace("\f", "\n")


COLUMN_GAP_RE = re.compile(r" {8,}")
ORPHAN_SUB_RE = re.compile(r"^\s*(\d{1,2})\.(\d{1,2})\.\s*$")
ORPHAN_LETTER_RE = re.compile(r"^\s*(\d{1,2})\.([A-Za-z])\.\s*$")
ORPHAN_TOP_RE = re.compile(r"^\s*(\d{1,2})\.\s*$")


def flatten_columns(text: str) -> str:
    """Single left-aligned stream: no centered blocks, no side-by-side columns."""
    out: list[str] = []
    for ln in text.splitlines():
        # Split space-padded dual columns (e.g. Mayor … City Administrator)
        if COLUMN_GAP_RE.search(ln):
            parts = [p.strip() for p in COLUMN_GAP_RE.split(ln) if p.strip()]
            if len(parts) >= 2:
                out.extend(parts)
                continue
        # Strip centering indent; collapse leftover multi-spaces inside the line
        s = ln.strip()
        if s:
            s = re.sub(r" {2,}", " ", s)
        out.append(s)
    return "\n".join(out)


def join_orphan_item_numbers(text: str) -> str:
    """Plain pdftotext often emits `7.` then a blank line then the title — join them."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        m = ORPHAN_SUB_RE.match(ln) or ORPHAN_LETTER_RE.match(ln) or ORPHAN_TOP_RE.match(ln)
        if m:
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n:
                title = lines[j].strip()
                # Don't swallow another orphan number as a title
                if not (
                    ORPHAN_SUB_RE.match(title)
                    or ORPHAN_LETTER_RE.match(title)
                    or ORPHAN_TOP_RE.match(title)
                ):
                    if ORPHAN_SUB_RE.match(ln):
                        mm = ORPHAN_SUB_RE.match(ln)
                        out.append(f"{int(mm.group(1))}.{int(mm.group(2))}. {title}")
                    elif ORPHAN_LETTER_RE.match(ln):
                        mm = ORPHAN_LETTER_RE.match(ln)
                        out.append(f"{int(mm.group(1))}.{mm.group(2).upper()}. {title}")
                    else:
                        mm = ORPHAN_TOP_RE.match(ln)
                        out.append(f"{int(mm.group(1))}. {title}")
                    i = j + 1
                    continue
        out.append(ln)
        i += 1
    return "\n".join(out)



def normalize_bullets_line(line: str) -> str:
    # Replace bullet glyph (+ optional following spaces) with "- "
    def repl(m: re.Match) -> str:
        # Preserve indent before the bullet
        return "- "

    # Only at start-of-content after indent
    return re.sub(r"(^[ \t]*)[•●▪◦‣][ \t]*", r"\1- ", line)


def is_running_header_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if CITY_LINE_RE.match(s):
        return True
    if AGENDA_HDR_RE.match(s):
        return True
    if PASSFAIL_HDR_RE.match(s):
        return True
    if AGENDA_WORD_RE.match(s):
        return True
    if DATE_HDR_RE.match(s):
        return True
    if PUBLIC_HEARING_HDR_RE.match(s) and len(s) < 90:
        return True
    if TIME_HDR_RE.match(s):
        return True
    return False


def strip_page_chrome_and_headers(text: str) -> str:
    """Remove Page N of M and repeated running headers (keep first banner)."""
    lines = text.splitlines()
    out: list[str] = []
    seen_running_cluster = False
    i = 0
    n = len(lines)

    def is_page(ln: str) -> bool:
        return bool(PAGE_ONLY_RE.match(ln) or PAGE_TRAIL_RE.match(ln))

    while i < n:
        ln = lines[i]
        # Drop page-number-only lines
        if is_page(ln):
            i += 1
            # After a page marker, skip a following running-header cluster
            # (City / Commission Agenda / Date [/ Public Hearing line] [/ time])
            if seen_running_cluster:
                while i < n and (not lines[i].strip() or is_running_header_line(lines[i])):
                    # Don't eat blank lines forever — only contiguous header block
                    if not lines[i].strip():
                        # peek: if next non-empty is still header, skip blank; else stop
                        j = i + 1
                        while j < n and not lines[j].strip():
                            j += 1
                        if j < n and is_running_header_line(lines[j]):
                            i += 1
                            continue
                        break
                    i += 1
            continue

        # Detect first running-header cluster (keep it) vs later ones (drop)
        if is_running_header_line(ln):
            # Gather cluster
            cluster = [ln]
            j = i + 1
            while j < n and (
                not lines[j].strip()
                or is_running_header_line(lines[j])
                or is_page(lines[j])
            ):
                if is_page(lines[j]):
                    j += 1
                    continue
                if not lines[j].strip():
                    # include one blank inside cluster only if more header follows
                    k = j + 1
                    while k < n and not lines[k].strip():
                        k += 1
                    if k < n and is_running_header_line(lines[k]):
                        cluster.append(lines[j])
                        j += 1
                        continue
                    break
                cluster.append(lines[j])
                j += 1

            # Heuristic: a "cluster" of 2+ header-ish lines is running chrome
            header_count = sum(1 for c in cluster if c.strip() and is_running_header_line(c))
            if header_count >= 2:
                if not seen_running_cluster:
                    # keep first (document title banner)
                    out.extend(cluster)
                    seen_running_cluster = True
                # else drop
                i = j
                continue
            # Single header-ish line alone — keep (might be body)
            out.append(ln)
            i += 1
            continue

        out.append(ln)
        i += 1

    return "\n".join(out)


def collapse_whitespace(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    out: list[str] = []
    blank_run = 0
    for ln in lines:
        if not ln.strip():
            blank_run += 1
            if blank_run <= 2:
                out.append("")
        else:
            blank_run = 0
            out.append(ln)
    # Trim leading/trailing blank lines
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out) + "\n"


def looks_like_top_item(num: str, title: str, indent: str) -> bool:
    n = int(num)
    if n < 1 or n > 30:
        return False
    # Reject years accidentally matching TOP_ITEM (e.g. "2023. The...")
    if len(num) == 4:
        return False
    # Body lists are usually deeply indented; top items ≤4 spaces
    if len(indent) > 4:
        return False
    t = title.strip()
    if not t:
        return False
    # Field labels aren't items
    if t.lower().rstrip(":") in {x.rstrip(":") for x in FIELD_LABELS}:
        return False
    # Strong signal: mostly uppercase section titles
    letters = [c for c in t if c.isalpha()]
    if letters:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio >= 0.6:
            return True
    # Known opening / closing phrases (mixed case ok)
    known = (
        "call to order",
        "moment of silence",
        "pledge of allegiance",
        "civility",
        "additions",
        "consent",
        "presentation",
        "proclamation",
        "resolution",
        "public hearing",
        "public comment",
        "comments from the public",
        "comments by the mayor",
        "adjournment",
        "awards",
        "announcement",
    )
    low = t.lower()
    if any(low.startswith(k) for k in known):
        return True
    # Reject Title-Case / sentence body lists ("1. Integration is an…").
    # Real top-level agenda sections are ALL CAPS or known phrases above.
    if t[0].islower():
        return False
    return False


def anchor_id(major: str, minor: Optional[str] = None, letter: Optional[str] = None) -> str:
    parts = ["item", str(int(major))]
    if minor is not None:
        parts.append(str(int(minor)))
    if letter is not None:
        parts.append(letter.lower())
    return "-".join(parts)


def promote_items(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    for ln in lines:
        # Sub-item first (more specific)
        m = SUB_ITEM_RE.match(ln)
        if m:
            indent, major, minor, _sp, title = m.groups()
            # Guard: major should be agenda-sized
            if 1 <= int(major) <= 30 and 0 <= int(minor) <= 99:
                aid = anchor_id(major, minor)
                label = f"{int(major)}.{int(minor)}. {title.strip()}"
                if out and out[-1].strip():
                    out.append("")
                out.append(f'<a id="{aid}"></a>')
                out.append(f"### {label}")
                out.append("")
                continue

        m = LETTER_ITEM_RE.match(ln)
        if m:
            indent, major, letter, _sp, title = m.groups()
            if 1 <= int(major) <= 30:
                aid = anchor_id(major, letter=letter)
                label = f"{int(major)}.{letter.upper()}. {title.strip()}"
                if out and out[-1].strip():
                    out.append("")
                out.append(f'<a id="{aid}"></a>')
                out.append(f"### {label}")
                out.append("")
                continue

        m = TOP_ITEM_RE.match(ln)
        if m:
            indent, major, _sp, title = m.groups()
            if looks_like_top_item(major, title, indent):
                aid = anchor_id(major)
                label = f"{int(major)}. {title.strip()}"
                if out and out[-1].strip():
                    out.append("")
                out.append(f'<a id="{aid}"></a>')
                out.append(f"## {label}")
                out.append("")
                continue

        out.append(normalize_bullets_line(ln))

    return "\n".join(out)




def reflow_joined(parts: list[str]) -> str:
    """Join soft-wrapped lines; fix simple end-of-line hyphenation."""
    if not parts:
        return ""
    buf = parts[0].strip()
    for raw in parts[1:]:
        s = raw.strip()
        if not s:
            continue
        if buf.endswith("-") and not buf.endswith("--") and s[0].islower():
            buf = buf[:-1] + s
        else:
            buf = buf + " " + s
    return buf


def is_field_or_section_label(s: str) -> bool:
    if match_item_field_label(s) is not None:
        return True
    low = s.lower().rstrip(":")
    if low in {x.rstrip(":") for x in FIELD_LABELS}:
        return True
    if TITLE_CASE_LABEL_RE.match(s) and not is_predominantly_upper(s):
        return True
    return False


def is_reflow_hard_start(s: str) -> bool:
    """Lines that must not be glued onto the previous paragraph."""
    if s.startswith("<a ") or s.startswith("#"):
        return True
    if match_item_field_label(s) is not None:
        return True
    if s.startswith("**RESOLUTION:**") or s.startswith("**ORDINANCE:**"):
        return True
    if is_legal_block_start(s):
        return True
    if is_field_or_section_label(s):
        return True
    if SUB_ITEM_RE.match(s) or LETTER_ITEM_RE.match(s):
        return True
    m = TOP_ITEM_RE.match(s)
    if m and looks_like_top_item(m.group(2), m.group(4), m.group(1)):
        return True
    if ORPHAN_SUB_RE.match(s) or ORPHAN_LETTER_RE.match(s) or ORPHAN_TOP_RE.match(s):
        return True
    return False


def reflow_soft_wraps(text: str) -> str:
    """Join PDF soft wraps into paragraphs; hard-break only on real boundaries."""
    lines = text.splitlines()
    out: list[str] = []
    buf: str | None = None

    def flush() -> None:
        nonlocal buf
        if buf is not None:
            out.append(buf)
            buf = None

    def join_onto(buf_s: str, nxt: str) -> str:
        if buf_s.endswith("-") and not buf_s.endswith("--") and nxt and nxt[0].islower():
            return buf_s[:-1] + nxt
        return buf_s + " " + nxt

    for idx, ln in enumerate(lines):
        s = ln.strip()
        if not s:
            # Soft-wrapped heading titles often have a blank before the
            # lowercase continuation ("### 7.4. … bicycles" / "" / "from the…").
            j = idx + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            nxt = lines[j].strip() if j < len(lines) else ""
            if (
                out
                and buf is None
                and out[-1].startswith("#")
                and not out[-1].rstrip("#").endswith(".")
                and nxt
                and not is_reflow_hard_start(nxt)
                and not nxt.startswith("- ")
                and not is_predominantly_upper(nxt)
            ):
                continue
            flush()
            out.append("")
            continue

        if s.startswith("> "):
            content = s[2:].strip()
            if buf is not None and buf.startswith("> "):
                buf = "> " + join_onto(buf[2:], content)
            else:
                flush()
                buf = "> " + content
            continue

        if s.startswith("- "):
            # New bullet; allow following soft-wrap lines to join
            flush()
            buf = s
            continue

        if is_reflow_hard_start(s):
            flush()
            out.append(s)
            continue

        # Soft-wrap continuation of a markdown heading title (item line wrapped in PDF)
        if (
            buf is None
            and out
            and out[-1].startswith("#")
            and not out[-1].endswith(".")
            and s
            and not s.startswith("- ")
            and not is_predominantly_upper(s)
            and not is_reflow_hard_start(s)
        ):
            # If this wrap line finishes the title and starts body ("Month. Mayor…"),
            # keep only the title fragment on the heading.
            m = re.match(r"^(.*\.)\s+([A-Z].*)$", s)
            if m:
                out[-1] = join_onto(out[-1], m.group(1))
                buf = m.group(2)
            else:
                out[-1] = join_onto(out[-1], s)
            continue

        if buf is None:
            buf = s
        elif buf.startswith("- "):
            buf = join_onto(buf, s)
        elif buf.startswith("> "):
            # Non-quote line ends quote paragraph
            flush()
            buf = s
        else:
            buf = join_onto(buf, s)

    flush()
    return "\n".join(out)


LEGAL_START_RE = re.compile(r"^(RESOLUTION|ORDINANCE)\s+NO\.", re.I)
TITLE_CASE_LABEL_RE = re.compile(r"^[A-Z][a-zA-Z0-9 /&()'.,-]{0,60}:$")


def is_predominantly_upper(s: str) -> bool:
    letters = [c for c in s if c.isalpha()]
    if len(letters) < 6:
        return False
    return (sum(1 for c in letters if c.isupper()) / len(letters)) >= 0.85


def is_legal_block_start(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("#") or s.startswith("<a ") or s.startswith(">"):
        return False
    if s.startswith("**RESOLUTION:**") or s.startswith("**ORDINANCE:**"):
        return False
    return bool(LEGAL_START_RE.match(s)) and is_predominantly_upper(s)


def is_legal_block_continuation(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith("#") or s.startswith("<a ") or s.startswith(">"):
        return False
    if s.startswith("**RESOLUTION:**") or s.startswith("**ORDINANCE:**"):
        return False
    low = s.lower().rstrip(":")
    if low in {x.rstrip(":") for x in FIELD_LABELS}:
        return False
    if TITLE_CASE_LABEL_RE.match(s) and not is_predominantly_upper(s):
        return False
    # Next legal doc starts a new block
    if LEGAL_START_RE.match(s):
        return False
    letters = [c for c in s if c.isalpha()]
    # PDF often wraps ALL-CAPS titles onto tiny lines ("AND", "POLICE", "(IPTM)").
    if letters and all(c.isupper() for c in letters):
        return True
    return is_predominantly_upper(s)


def isolate_allcaps_legal_blocks(text: str) -> str:
    """ALL-CAPS resolution/ordinance runs become standalone marked blocks."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        if is_legal_block_start(ln):
            kind = "RESOLUTION" if ln.strip().upper().startswith("RESOLUTION") else "ORDINANCE"
            block = [ln.strip()]
            i += 1
            while i < n:
                if not lines[i].strip():
                    # Page breaks often insert blanks mid-resolution; keep going if
                    # the next non-empty line is still ALL-CAPS legal text.
                    j = i + 1
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n and is_legal_block_continuation(lines[j]):
                        i = j
                        continue
                    break
                if is_legal_block_continuation(lines[i]):
                    block.append(lines[i].strip())
                    i += 1
                    continue
                break
            # blank before
            if out and out[-1].strip():
                out.append("")
            out.append(f"**{kind}:**")
            out.append("")
            out.append(f"> {reflow_joined(block)}")
            out.append("")
            continue
        out.append(ln)
        i += 1
    return "\n".join(out)



ITEM_FIELD_LABELS = [
    (re.compile(r"^Originating Department\s*:?\s*$", re.I), "Originating Department"),
    (re.compile(r"^Department\s*:?\s*$", re.I), "Originating Department"),
    (re.compile(r"^Ordinance\s*/\s*Resolution\s*:?\s*$", re.I), "__ORD_RES__"),
    (re.compile(r"^Background Information\s*:?\s*$", re.I), "Background"),
    (re.compile(r"^Background\s*:?\s*$", re.I), "Background"),
    (re.compile(r"^Fiscal(?:\s+Note|\s+Impact)?\s*:?\s*$", re.I), "Fiscal Impact"),
    (re.compile(r"^Recommended Action\s*:?\s*$", re.I), "Recommended Action"),
    (re.compile(r"^Attachments?\s*:?\s*$", re.I), "Attachments"),
    (re.compile(r"^Presenter\s*:?\s*$", re.I), "Presenter"),
    (re.compile(r"^Sponsor\s*:?\s*$", re.I), "Sponsor"),
]


def match_item_field_label(s: str) -> str | None:
    s = s.strip()
    for rx, name in ITEM_FIELD_LABELS:
        if rx.match(s):
            return name
    return None


def promote_item_field_sections(text: str) -> str:
    """Turn Originating Department / Resolution / Background labels into #### subsections."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)

    def peek_nonempty(start: int) -> tuple[int, str]:
        j = start
        while j < n and not lines[j].strip():
            j += 1
        if j >= n:
            return j, ""
        return j, lines[j].strip()

    while i < n:
        raw = lines[i]
        s = raw.strip()
        label = match_item_field_label(s) if s else None
        if label == "__ORD_RES__":
            j, nxt = peek_nonempty(i + 1)
            kind = "Ordinance" if nxt.startswith("**ORDINANCE:") else "Resolution"
            if out and out[-1].strip():
                out.append("")
            out.append(f"#### {kind}")
            out.append("")
            i += 1
            continue
        if label:
            if out and out[-1].strip():
                out.append("")
            out.append(f"#### {label}")
            out.append("")
            j, nxt = peek_nonempty(i + 1)
            # Originating Department value is usually the next short line
            if label == "Originating Department" and nxt and match_item_field_label(nxt) is None:
                if not nxt.startswith("#") and not nxt.startswith("**") and not nxt.startswith("<a "):
                    out.append(nxt)
                    out.append("")
                    i = j + 1
                    continue
            i += 1
            continue
        out.append(raw)
        i += 1
    return "\n".join(out)


def clean_extract(raw: str) -> str:
    text = drop_formfeeds(raw)
    text = flatten_columns(text)
    text = join_orphan_item_numbers(text)
    text = strip_page_chrome_and_headers(text)
    # Normalize bullets on non-item lines happens inside promote; also do a pass
    # before promote for lines that won't match items
    text = "\n".join(normalize_bullets_line(ln) for ln in text.splitlines())
    text = collapse_whitespace(text)
    text = promote_items(text)
    text = isolate_allcaps_legal_blocks(text)
    text = reflow_soft_wraps(text)
    text = promote_item_field_sections(text)
    text = collapse_whitespace(text)
    return text


def pdf_link_label(url: str) -> str:
    return url.rstrip("/").split("/")[-1] or "official.pdf"


def render_markdown(meta: dict[str, str], body: str) -> str:
    date = meta.get("date", "")
    doc_type = meta.get("doc_type", "agenda")
    title = meta.get("title", "City Commission Document")
    meeting = meta.get("meeting", "")
    official_pdf = meta.get("official_pdf", "")
    retrieved = meta.get("retrieved", "")
    notes = meta.get("notes", "")
    kind = meta.get("kind", "")

    fm_lines = ["---", f"date: {date}", f"doc_type: {doc_type}", f"title: {title}"]
    if meeting:
        fm_lines.append(f"meeting: {meeting}")
    if kind:
        fm_lines.append(f"kind: {kind}")
    if official_pdf:
        fm_lines.append(f"official_pdf: {official_pdf}")
    if retrieved:
        fm_lines.append(f"retrieved: {retrieved}")
    fm_lines.append(f"extractor: {EXTRACTOR}")
    if notes:
        # keep notes compact
        fm_lines.append("notes: >")
        for note_line in notes.strip().splitlines() or [
            "Plain-text extract of the official PDF. Binary PDF not stored in this repo."
        ]:
            fm_lines.append(f"  {note_line.strip()}")
    else:
        fm_lines.append("notes: >")
        fm_lines.append(
            "  Plain-text extract of the official PDF. Binary PDF not stored in this repo."
        )
    fm_lines.append("---")
    fm_lines.append("")

    h1 = f"# {title}"
    if date and date not in title:
        h1 = f"# {title} — {date}"

    parts = [
        "\n".join(fm_lines),
        h1,
        "",
    ]
    if official_pdf:
        label = pdf_link_label(official_pdf)
        parts.append(f"**Official PDF (wpb.org):** [{label}]({official_pdf})")
        parts.append("")
    parts.append(
        "Text extract below is for search and deep-linking. "
        "The official PDF is authoritative."
    )
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append(body.rstrip())
    parts.append("")
    return "\n".join(parts)


def infer_meeting(meta: dict[str, str], title: str) -> str:
    if meta.get("meeting"):
        return meta["meeting"]
    t = (title or meta.get("title") or "").lower()
    if "special" in t and "budget" in t:
        return meta.get("title") or "Special City Commission"
    if "special" in t:
        return meta.get("title") or "Special City Commission"
    if "pass" in (meta.get("doc_type") or "") or "pass/fail" in t or "pass-fail" in t:
        return "Regular City Commission Meeting"
    return "Regular City Commission Meeting"


def process_file(
    path: Path,
    *,
    out: Optional[Path] = None,
    overrides: Optional[dict[str, str]] = None,
) -> Path:
    text = path.read_text(encoding="utf-8", errors="replace")
    meta, body = parse_frontmatter(text)
    if overrides:
        meta.update({k: v for k, v in overrides.items() if v})

    # If no frontmatter (raw txt), body is whole file
    if not meta and not text.startswith("---"):
        body = text

    raw = extract_raw_body(body) if meta else body
    cleaned = clean_extract(raw)

    # Defaults from path
    if not meta.get("date"):
        # parent folder YYYY-MM-DD
        if re.match(r"\d{4}-\d{2}-\d{2}$", path.parent.name):
            meta["date"] = path.parent.name
    if not meta.get("doc_type"):
        name = path.stem.lower()
        if "pass" in name:
            meta["doc_type"] = "pass-fail"
        elif "minute" in name:
            meta["doc_type"] = "minutes"
        else:
            meta["doc_type"] = "agenda"
    if not meta.get("title"):
        if meta.get("doc_type") == "pass-fail":
            meta["title"] = "Pass/Fail — City Commission Agenda"
        else:
            meta["title"] = "Final City Commission Agenda"
    meta["meeting"] = infer_meeting(meta, meta.get("title", ""))
    meta["extractor"] = EXTRACTOR

    rendered = render_markdown(meta, cleaned)
    dest = out or path
    dest.write_text(rendered, encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="Existing .md or raw .txt extract")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--date")
    p.add_argument("--doc-type")
    p.add_argument("--title")
    p.add_argument("--meeting")
    p.add_argument("--official-pdf")
    p.add_argument("--retrieved")
    p.add_argument("--kind")
    args = p.parse_args(argv)

    overrides = {
        k: v
        for k, v in {
            "date": args.date,
            "doc_type": args.doc_type,
            "title": args.title,
            "meeting": args.meeting,
            "official_pdf": args.official_pdf,
            "retrieved": args.retrieved,
            "kind": args.kind,
        }.items()
        if v
    }
    dest = process_file(args.input, out=args.out, overrides=overrides)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
