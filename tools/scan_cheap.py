"""Find solved-but-unformalized JSP problems whose resolution is LIKELY a small
finite verification: a short yes/no / small-answer question in an elementary
area, with no asymptotic language in the statement.

This is a triage aid only - every hit still needs the primary source checked.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "_ref-jsp-catalog"
ANCHOR = re.compile(r'<a id="(JSP-\d{6})"></a>')
ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", re.M)

ASYMP = ("asymptotic", "sufficiently large", "density", "grows", "O(",
         "Omega", "tends to", "for large", "infinitely many", "unbounded",
         "limsup", "liminf")
AREAS = ("Number theory", "Combinatorics", "Graph theory", "Geometry",
         "Diophantine", "Group theory", "Algebra")
HEAD = re.compile(r"^(Are|Is|Can|Does|Must|Do|Which|When|How many|What|If)")


def main() -> int:
    rows = []
    for p in sorted(CAT.glob("catalog-*.md")):
        t = p.read_text(encoding="utf-8")
        parts = ANCHOR.split(t)
        for i in range(1, len(parts), 2):
            jid, body = parts[i], parts[i + 1]
            end = body.find("<a id=")
            sec = body[:end] if end != -1 else body
            f: dict[str, str] = {}
            for m in ROW.finditer(sec):
                k, v = m.group(1).strip(), m.group(2).strip()
                if set(k) <= {"-", " ", "·"} or k == "Field":
                    continue
                f.setdefault(k, v)
            st = f.get("Current status", "")
            lean = f.get("Lean proof", "").strip()
            if not (st.startswith("Solved") and lean == "No"):
                continue
            desc = f.get("Problem description", "")
            area = f.get("Mathematical area", "")
            if any(a.lower() in desc.lower() for a in ASYMP):
                continue
            if not any(a in area for a in AREAS):
                continue
            if len(desc) > 170:
                continue
            if not HEAD.match(desc):
                continue
            rows.append((jid, area, desc))

    print(f"candidates: {len(rows)}")
    for jid, area, desc in rows:
        print(f"{jid}  [{area}]")
        print(f"    {desc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
