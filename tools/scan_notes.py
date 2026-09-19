"""Find solved-but-unformalized JSP problems whose review notes describe an
EXPLICIT small witness (a concrete number, set, graph, ...).

JSP-000301's review note spelled out 12167 = 23^3 and 12168 = 2^3*3^2*13^2 --
that is the shape we want. Problems whose note contains explicit arithmetic
are prime candidates for a finite verification.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "_ref-jsp-catalog"
ANCHOR = re.compile(r'<a id="(JSP-\d{6})"></a>')
ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", re.M)
# explicit-arithmetic signals
SIG = ("=", "\\times", "x", "\\cdot", "counterexample", "disproved",
       "neither", "not a", "example")
NUM = re.compile(r"\d{2,}")


def main() -> int:
    hits = []
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
            rn = re.search(r"### Review notes(.*?)(?=\n<a id=|\Z)", sec, re.S)
            if not rn:
                continue
            note = rn.group(1)
            # does the note contain explicit arithmetic (a big number + '=')?
            big = NUM.findall(note)
            if len(big) >= 2 and ("=" in note or "counterexample" in note.lower()):
                m = re.search(r"^##\s+JSP-\d{6}\s*·\s*(.*)$", sec, re.M)
                hits.append((jid, m.group(1).strip() if m else "",
                             " ".join(note.split())[:400]))

    print(f"solved+unformalized WITH review notes containing explicit arithmetic: {len(hits)}")
    for jid, title, note in hits:
        print("=" * 90)
        print(f"{jid}  {title}")
        print(f"  note: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
