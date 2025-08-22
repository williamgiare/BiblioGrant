#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import bibtexparser

# =========================
# LaTeX -> Unicode helpers
# =========================

_LATEX_SIMPLE = {
    r"\textquoteright": "’",
    r"\textquoteleft": "‘",
    r"\textendash": "–",
    r"\textemdash": "—",
    r"\textquotesingle": "’",
    r"``": "“",
    r"''": "”",
    r"\/": "",              # italic correction
    r"\ensuremath": "",     # remove math wrapper
    r"\&": "&",
    r"\%": "%",
    r"\_": "_",
    r"\#": "#",
}

# Accent mapping: \'e, \`e, \"o, \~n, \c{c}, \v{c}, etc.
_ACCENT_MAP = {
    "'": {"a":"á","e":"é","i":"í","o":"ó","u":"ú","y":"ý","A":"Á","E":"É","I":"Í","O":"Ó","U":"Ú","Y":"Ý"},
    "`": {"a":"à","e":"è","i":"ì","o":"ò","u":"ù","A":"À","E":"È","I":"Ì","O":"Ò","U":"Ù"},
    "^": {"a":"â","e":"ê","i":"î","o":"ô","u":"û","A":"Â","E":"Ê","I":"Î","O":"Ô","U":"Û"},
    '"': {"a":"ä","e":"ë","i":"ï","o":"ö","u":"ü","y":"ÿ","A":"Ä","E":"Ë","I":"Ï","O":"Ö","U":"Ü","Y":"Ÿ"},
    "~": {"a":"ã","o":"õ","n":"ñ","A":"Ã","O":"Õ","N":"Ñ"},
    "c": {"c":"ç","C":"Ç"},
    "v": {"c":"č","s":"š","z":"ž","C":"Č","S":"Š","Z":"Ž"},
    "H": {"o":"ő","u":"ű","O":"Ő","U":"Ű"},
    "k": {"a":"ą","e":"ę","A":"Ą","E":"Ę"},
    "u": {"a":"ă","A":"Ă"},
    "r": {"a":"å","A":"Å"},
    "=": {"a":"ā","e":"ē","i":"ī","o":"ō","u":"ū","A":"Ā","E":"Ē","I":"Ī","O":"Ō","U":"Ū"},
    ".": {"z":"ż","Z":"Ż"},
}
_DOTLESS = {"\\i": "ı", "\\j": "ȷ"}

# Common Greek macros
_GREEK = {
    r"\alpha":"α", r"\beta":"β", r"\gamma":"γ", r"\delta":"δ",
    r"\epsilon":"ε", r"\varepsilon":"ε", r"\zeta":"ζ", r"\eta":"η",
    r"\theta":"θ", r"\vartheta":"ϑ", r"\iota":"ι", r"\kappa":"κ",
    r"\lambda":"λ", r"\mu":"μ", r"\nu":"ν", r"\xi":"ξ",
    r"\pi":"π", r"\varpi":"ϖ", r"\rho":"ρ", r"\varrho":"ϱ",
    r"\sigma":"σ", r"\varsigma":"ς", r"\tau":"τ", r"\upsilon":"υ",
    r"\phi":"φ", r"\varphi":"ϕ", r"\chi":"χ", r"\psi":"ψ", r"\omega":"ω",
    r"\Gamma":"Γ", r"\Delta":"Δ", r"\Theta":"Θ", r"\Lambda":"Λ",
    r"\Xi":"Ξ", r"\Pi":"Π", r"\Sigma":"Σ", r"\Upsilon":"Υ",
    r"\Phi":"Φ", r"\Psi":"Ψ", r"\Omega":"Ω",
}

_ACCENT_CMD_RE = re.compile(
    r"""\\(?P<acc>['"`^~=.Hkvur])\{?(?P<char>\\i|\\j|[A-Za-z])\}?""",
    flags=re.UNICODE
)

def _apply_accent(m):
    acc = m.group("acc")
    ch  = m.group("char")
    ch  = _DOTLESS.get(ch, ch)
    return _ACCENT_MAP.get(acc, {}).get(ch, ch)

def latex_to_unicode(s: str) -> str:
    """Convert common LaTeX accents, quotes, Greek letters into Unicode."""
    if not s:
        return ""
    for k, v in _LATEX_SIMPLE.items():
        s = s.replace(k, v)
    s = _ACCENT_CMD_RE.sub(_apply_accent, s)
    for k, v in _GREEK.items():
        s = s.replace(k, v)
    s = s.replace("$", "")
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _clean(s: str) -> str:
    return latex_to_unicode(s) if s else ""

# =========================
# Author formatting
# =========================

def _split_authors(author_field: str):
    return [a.strip() for a in author_field.replace("\n", " ").split(" and ") if a.strip()]

def _format_author_name(name: str) -> str:
    """
    Convert:
      - 'Last, First M.' -> 'First M. Last'
      - 'First M. Last'  -> unchanged
    """
    name = _clean(name)
    parts = [p.strip() for p in name.split(",")]
    if len(parts) == 1:
        toks = parts[0].split()
        if len(toks) <= 1:
            return parts[0]
        last = toks[-1]
        firsts = " ".join(toks[:-1])
        return f"{firsts} {last}"
    else:
        last = parts[0]
        firsts = parts[-1]
        middle = " ".join(p for p in parts[1:-1] if p)
        if middle:
            return f"{firsts} {middle} {last}".strip()
        return f"{firsts} {last}".strip()

def _format_authors(entry):
    a = entry.get("author") or entry.get("editor") or ""
    if not a:
        return ""
    authors = [_format_author_name(x) for x in _split_authors(a)]
    return ", ".join(authors)

def _first_author(entry):
    a = entry.get("author") or entry.get("editor") or ""
    if not a:
        return ""
    parts = _split_authors(a)
    return _format_author_name(parts[0]), len(parts)

# =========================
# Date & sorting helpers
# =========================

def _year(entry):
    """Return year from 'year' or 'date' fields if available."""
    return entry.get("year") or (entry.get("date", "")[:4] if entry.get("date") else "")

def _ensure_dot(s: str) -> str:
    s = s.strip()
    return s if s.endswith((".", "!", "?")) else s + "."

def _is_preprint(entry):
    """
    Identify preprints:
      - ENTRYTYPE in {'article','unpublished','misc'}
      - and NO journal/journaltitle
    (regardless of DOI presence)
    """
    etype = (entry.get("ENTRYTYPE") or "").lower()
    if etype not in {"article", "unpublished", "misc"}:
        return False
    has_journal = bool(entry.get("journal") or entry.get("journaltitle"))
    return not has_journal

def _repo_id(entry):
    repo = entry.get("eprinttype") or entry.get("archiveprefix") or "arXiv"
    eid  = entry.get("eprint", "")
    ecls = entry.get("eprintclass", "")
    core = f"{repo}:{eid}" if eid else repo
    if repo.lower() == "arxiv" and ecls:
        core += f" [{ecls}]"
    return core

def _repo_id_compact(entry):
    """Compact arXiv id without classification brackets."""
    repo = entry.get("eprinttype") or entry.get("archiveprefix") or "arXiv"
    eid  = entry.get("eprint", "")
    if repo:
        repo = repo.capitalize() if repo.lower() == "arxiv" else repo
    return f"{repo}:{eid}" if eid else repo or "preprint"

def _parse_arxiv_yymm(eprint: str):
    """
    Parse arXiv ID to extract (year, month, sequence).
    Supports:
      - New format: yymm.nnnnn (since 2007)
      - Old format: astro-ph/YYMMnnn
    """
    if not eprint:
        return None
    eprint = eprint.strip()

    # New format
    m = re.match(r'^(?P<yy>\d{2})(?P<mm>\d{2})\.(?P<seq>\d{4,5})$', eprint)
    if m:
        yy = int(m.group("yy"))
        mm = int(m.group("mm"))
        seq = int(m.group("seq"))
        year = 2000 + yy
        mm = max(1, min(mm, 12))
        return (year, mm, seq)

    # Old format
    m = re.match(r'^[a-z\-]+\/(?P<yy>\d{2})(?P<mm>\d{2})(?P<seq>\d{3,4})$', eprint, flags=re.IGNORECASE)
    if m:
        yy = int(m.group("yy"))
        mm = int(m.group("mm"))
        seq = int(m.group("seq"))
        year = 1900 + yy if yy >= 90 else 2000 + yy
        mm = max(1, min(mm, 12))
        return (year, mm, seq)

    return None

def _sort_key_publication(e):
    """Sort by publication year (ascending in key; flip with reverse flag)."""
    y = _year(e)
    m = re.search(r"\d{4}", y or "")
    yi = int(m.group(0)) if m else -1
    sec = (_clean(e.get("author","") or e.get("editor","") or "") + " " + _clean(e.get("title","") or "")).lower()
    return (yi, sec)

def _sort_key_preprint(e):
    """Sort by arXiv yymm (ascending in key; flip with reverse flag)."""
    parsed = _parse_arxiv_yymm(e.get("eprint","") or "")
    if parsed:
        year, month, seq = parsed
        primary = (year, month, seq)
    else:
        y = _year(e)
        m = re.search(r"\d{4}", y or "")
        yi = int(m.group(0)) if m else -1
        primary = (yi, 0, 0)
    sec = (_clean(e.get("author","") or e.get("editor","") or "") + " " + _clean(e.get("title","") or "")).lower()
    return (*primary, sec)

# =========================
# Formatters (full)
# =========================

def _format_article(e):
    authors = _format_authors(e)
    title   = _clean(e.get("title",""))
    jt      = _clean(e.get("journaltitle") or e.get("journal",""))
    year    = _year(e)
    vol     = _clean(e.get("volume",""))
    num     = _clean(e.get("number",""))
    pages   = _clean(e.get("pages",""))
    doi     = (e.get("doi","") or "").strip()
    url     = (e.get("url","") or "").strip()

    core = f'{authors}. "{title}."'
    if jt:   core += f" {jt} {year}"
    elif year: core += f" {year}"
    if vol:   core += f", {vol}"
    if num:   core += f"({num})"
    if pages: core += f": {pages}"
    core = _ensure_dot(core)
    if doi: core += f" DOI: {doi}"
    if url: core += f" URL: {url}"
    return core

def _format_preprint(e):
    authors = _format_authors(e)
    title   = _clean(e.get("title",""))
    repo_id = _repo_id(e)
    year    = _year(e)
    doi     = (e.get("doi","") or "").strip()
    url     = (e.get("url","") or "").strip()

    core = f'{authors}. "{title}." Preprint, {repo_id}'
    if year: core += f", {year}"
    core = _ensure_dot(core)
    if doi: core += f" DOI: {doi}"
    if url: core += f" URL: {url}"
    return core

def _format_generic(e):
    authors = _format_authors(e)
    title   = _clean(e.get("title",""))
    year    = _year(e)
    doi     = (e.get("doi","") or "").strip()
    url     = (e.get("url","") or "").strip()

    core = f'{authors}. "{title}."'
    if year: core += f" {year}"
    core = _ensure_dot(core)
    if doi: core += f" DOI: {doi}"
    if url: core += f" URL: {url}"
    return core

# =========================
# Formatters (compact)
# =========================

def _venue_for_compact(e):
    """Pick the best venue string for compact mode (journal > booktitle > publisher > org/institution/howpublished)."""
    return _clean(
        e.get("journaltitle")
        or e.get("journal")
        or e.get("booktitle")
        or e.get("publisher")
        or e.get("organization")
        or e.get("institution")
        or e.get("howpublished")
        or ""
    )

def _format_compact_published(e):
    first, n = _first_author(e)
    etal = " et al." if n and n > 1 else ""
    venue = _venue_for_compact(e)
    year  = _year(e)
    vol   = _clean(e.get("volume",""))
    num   = _clean(e.get("number",""))
    pages = _clean(e.get("pages",""))

    tail = venue
    if year:
        tail += f" {year}"
    inner = ""
    if vol:
        inner += f"{vol}"
    if num:
        inner += f"({num})"
    if pages:
        inner += (": " if inner else ": ") + pages
    if inner:
        tail += f", {inner}"

    return f"{first}{etal}, {tail}".strip()

def _format_compact_preprint(e):
    first, n = _first_author(e)
    etal = " et al." if n and n > 1 else ""
    arx = _repo_id_compact(e)
    return f"{first}{etal}, {arx}".strip()

def _format_entry(e, compact=False):
    if compact:
        if _is_preprint(e):
            return _format_compact_preprint(e)
        return _format_compact_published(e)
    else:
        if _is_preprint(e):
            return _format_preprint(e)
        et = (e.get("ENTRYTYPE") or "").lower()
        if et == "article":
            return _format_article(e)
        return _format_generic(e)

# =========================
# Core builder used by print/save
# =========================

def _build_biblio_lines(
    bibfile,
    order_by="keep_bib",
    reverse=False,
    group_preprints_on_publication=True,
    compact=False,
):
    """Build the list of lines to output, honoring all options."""
    with open(bibfile, "r", encoding="utf-8") as f:
        db = bibtexparser.load(f)
    entries = db.entries

    if order_by == "keep_bib":
        ordered = entries[::-1] if reverse else entries
        lines = [_format_entry(e, compact=compact) for e in ordered]

    elif order_by == "preprint_date":
        ordered = sorted(entries, key=_sort_key_preprint, reverse=not reverse)
        lines = [_format_entry(e, compact=compact) for e in ordered]

    else:  # publication_date
        if group_preprints_on_publication:
            preprints = [e for e in entries if _is_preprint(e)]
            pubs      = [e for e in entries if not _is_preprint(e)]

            preprints_sorted = sorted(preprints, key=_sort_key_preprint,    reverse=not reverse)
            pubs_sorted      = sorted(pubs,      key=_sort_key_publication, reverse=not reverse)

            lines = []
            if preprints_sorted:
                lines.append("PREPRINTS")
                lines.append("")
                for i, e in enumerate(preprints_sorted):
                    lines.append(_format_entry(e, compact=compact))
                    if i != len(preprints_sorted) - 1:
                        lines.append("")
            if pubs_sorted:
                if lines:
                    lines.append("")
                lines.append("PUBLICATIONS")
                lines.append("")
                for i, e in enumerate(pubs_sorted):
                    lines.append(_format_entry(e, compact=compact))
                    if i != len(pubs_sorted) - 1:
                        lines.append("")
        else:
            ordered = sorted(entries, key=_sort_key_publication, reverse=not reverse)
            lines = [_format_entry(e, compact=compact) for e in ordered]

    return lines

# =========================
# Public API
# =========================

def print_biblio(
    bibfile,
    order_by="keep_bib",
    reverse=False,
    return_lines=False,
    group_preprints_on_publication=True,
    compact=False,
):
    """
    Print bibliography (stdout). See save_biblio for parameters.
    """
    lines = _build_biblio_lines(
        bibfile=bibfile,
        order_by=order_by,
        reverse=reverse,
        group_preprints_on_publication=group_preprints_on_publication,
        compact=compact,
    )

    if return_lines:
        return lines

    for i, line in enumerate(lines):
        print(line)
        if i < len(lines) - 1:
            print()  # preserve blank lines

def save_biblio(
    bibfile,
    out_path,
    order_by="keep_bib",
    reverse=False,
    group_preprints_on_publication=True,
    compact=False,
):
    """
    Save bibliography to a text file, with the same behavior as print_biblio.

    Args:
        bibfile: path to the .bib file
        out_path: path to the output .txt file
        order_by: "keep_bib" (default) | "publication_date" | "preprint_date"
        reverse: reverse the chosen ordering (oldest-first; reverse .bib order)
        group_preprints_on_publication: when ordering by publication_date,
            print a 'PREPRINTS' section first, then 'PUBLICATIONS' (default True)
        compact: compact entries (e.g., 'First Author et al., Venue Year, Vol(Issue): Pages'
                 or 'First Author et al., arXiv:ID' for preprints)
    """
    lines = _build_biblio_lines(
        bibfile=bibfile,
        order_by=order_by,
        reverse=reverse,
        group_preprints_on_publication=group_preprints_on_publication,
        compact=compact,
    )
    # Write with trailing newline and preserved blank lines
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")