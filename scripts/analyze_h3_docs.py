"""Thorough structural analysis of h3geo.org docs (from uber/h3 website/docs)."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

DOCS = Path(r"d:\OfficeWork\h3-lib\.refs\h3\website\docs")
OUT = Path(r"d:\OfficeWork\h3-lib\scripts\h3_docs_analysis.json")

HEADING = re.compile(r"^(#{1,4})\s+(.+?)\s*$", re.M)
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
FUNC = re.compile(r"^##\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", re.M)
SLUG = re.compile(r"^slug:\s*(.+)$", re.M)
TITLE = re.compile(r"^title:\s*(.+)$", re.M)
ID = re.compile(r"^id:\s*(.+)$", re.M)
FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)


def strip_frontmatter(text: str) -> tuple[dict, str]:
    meta: dict = {}
    m = FRONT.match(text)
    body = text
    if m:
        fm = m.group(1)
        body = text[m.end() :]
        for key, rx in (("id", ID), ("title", TITLE), ("slug", SLUG)):
            mm = rx.search(fm)
            if mm:
                meta[key] = mm.group(1).strip().strip("'\"")
    return meta, body


def analyze_file(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    meta, body = strip_frontmatter(raw)
    rel = path.relative_to(DOCS).as_posix()
    section = rel.split("/")[0] if "/" in rel else "root"
    headings = [(len(h.group(1)), h.group(2).strip()) for h in HEADING.finditer(body)]
    funcs = FUNC.findall(body)
    links = LINK.findall(body)
    ext_links = sorted({u for _, u in links if u.startswith("http")})
    int_links = sorted({u for _, u in links if not u.startswith("http") and not u.startswith("#")})
    words = len(re.findall(r"\b\w+\b", body))
    return {
        "path": rel,
        "section": section,
        "url": f"https://h3geo.org/docs/{meta.get('slug', rel).lstrip('/')}"
        if meta.get("slug")
        else f"https://h3geo.org/docs/{rel.rsplit('.', 1)[0]}",
        "id": meta.get("id"),
        "title": meta.get("title") or (headings[0][1] if headings else path.stem),
        "slug": meta.get("slug"),
        "bytes": path.stat().st_size,
        "words": words,
        "n_headings": len(headings),
        "headings": [h for _, h in headings[:30]],
        "api_functions": funcs,
        "n_api_functions": len(funcs),
        "external_links": ext_links[:40],
        "n_external_links": len(ext_links),
        "internal_links": int_links[:40],
        "preview": body.strip()[:500],
    }


def main() -> None:
    files = sorted(
        [p for p in DOCS.rglob("*") if p.suffix.lower() in {".md", ".mdx"} and p.name != "README.md"]
    )
    pages = [analyze_file(p) for p in files]

    by_section: dict[str, list] = defaultdict(list)
    for p in pages:
        by_section[p["section"]].append(
            {"title": p["title"], "path": p["path"], "url": p["url"], "funcs": p["n_api_functions"], "words": p["words"]}
        )

    all_funcs = []
    for p in pages:
        all_funcs.extend(p["api_functions"])

    ext_counter: Counter[str] = Counter()
    for p in pages:
        for u in p["external_links"]:
            # host only
            host = re.sub(r"^https?://", "", u).split("/")[0]
            ext_counter[host] += 1

    # Map API pages specially
    api_catalog = {
        p["path"]: p["api_functions"]
        for p in pages
        if p["section"] == "api"
    }

    report = {
        "source": "https://h3geo.org/docs (content from github.com/uber/h3 website/docs)",
        "page_count": len(pages),
        "sections": {k: len(v) for k, v in sorted(by_section.items())},
        "by_section": dict(by_section),
        "api_function_total": len(all_funcs),
        "api_functions_unique": sorted(set(all_funcs)),
        "api_catalog": api_catalog,
        "external_hosts": ext_counter.most_common(30),
        "pages": pages,
        "doc_ia": {
            "root": ["Introduction", "Installation", "Quickstart"],
            "highlights": "Why H3: indexing, joining, aggregation, flow modeling, ML",
            "comparisons": "S2, Geohash, Hexbin, Admin boundaries, Placekey",
            "core_library": "Architecture, coordinate systems, algorithms, bindings, testing",
            "api": "Indexing, inspection, traversal, hierarchy, regions, directed edge, vertex, misc",
            "library": "Terminology, H3Index modes, resolution table, errors, 3.x migration",
            "community": "Bindings, libraries, applications, tutorials",
        },
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"pages={len(pages)} funcs={len(set(all_funcs))} sections={dict((k,len(v)) for k,v in by_section.items())}")
    print("API pages:")
    for path, funcs in api_catalog.items():
        print(f"  {path}: {len(funcs)} -> {funcs}")


if __name__ == "__main__":
    main()
