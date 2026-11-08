"""Extract structure and key content from uber/h3-py-notebooks."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(r"d:\OfficeWork\h3-lib\.refs\h3-py-notebooks")
H3_API = re.compile(r"\bh3\.([a-zA-Z_][a-zA-Z0-9_]*)\b")
IMPORT = re.compile(r"^\s*(?:from\s+(\S+)\s+import|import\s+(\S+))", re.M)


def summarize_nb(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    cells = data.get("cells", [])
    md_titles = []
    md_preview = []
    code_preview = []
    apis: Counter[str] = Counter()
    imports: Counter[str] = Counter()
    code_lines = 0
    md_chars = 0
    has_output = 0

    for cell in cells:
        src = "".join(cell.get("source", []))
        ctype = cell.get("cell_type")
        if ctype == "markdown":
            md_chars += len(src)
            for line in src.splitlines():
                if line.startswith("#"):
                    md_titles.append(line.strip())
            if len(md_preview) < 8 and src.strip():
                md_preview.append(src.strip()[:400])
        elif ctype == "code":
            code_lines += src.count("\n") + (1 if src and not src.endswith("\n") else 0)
            apis.update(H3_API.findall(src))
            for m in IMPORT.finditer(src):
                mod = m.group(1) or m.group(2)
                imports[mod.split(".")[0].strip(" ,")] += 1
            if cell.get("outputs"):
                has_output += 1
            if len(code_preview) < 6 and src.strip():
                code_preview.append(src.strip()[:500])

    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "n_cells": len(cells),
        "n_md": sum(1 for c in cells if c.get("cell_type") == "markdown"),
        "n_code": sum(1 for c in cells if c.get("cell_type") == "code"),
        "code_lines": code_lines,
        "md_chars": md_chars,
        "cells_with_output": has_output,
        "titles": md_titles[:40],
        "top_h3_apis": apis.most_common(40),
        "top_imports": imports.most_common(25),
        "md_preview": md_preview,
        "code_preview": code_preview,
        "all_h3_apis": sorted(apis),
        "api_counts": dict(apis),
    }


def main() -> None:
    notebooks = sorted(ROOT.rglob("*.ipynb"))
    report = {
        "repo": "https://github.com/uber/h3-py-notebooks.git",
        "notebook_count": len(notebooks),
        "notebooks": [summarize_nb(p) for p in notebooks],
    }
    # Aggregate API usage across all notebooks
    total: Counter[str] = Counter()
    for nb in report["notebooks"]:
        total.update(nb["api_counts"])
    report["aggregate_h3_apis"] = total.most_common(80)
    out = Path(r"d:\OfficeWork\h3-lib\scripts\h3_notebooks_analysis.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Notebooks: {len(notebooks)}")
    for nb in report["notebooks"]:
        print(
            f"- {nb['path']}: cells={nb['n_cells']} code_lines={nb['code_lines']} "
            f"h3_apis={len(nb['all_h3_apis'])} size={nb['bytes']}"
        )
    print("Top APIs:", report["aggregate_h3_apis"][:20])


if __name__ == "__main__":
    main()
