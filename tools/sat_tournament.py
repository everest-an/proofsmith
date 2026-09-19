"""SAT encoding: find a tournament on 13 vertices with no transitive
subtournament of order 5 (the Reid-Parker 1970 counterexample).

Variables: one per unordered pair {i,j}, i<j.  var = 1 + index(pair).
  var true  <=>  i -> j
Constraint: for every 5-subset and every one of its 120 linear orders,
  at least one of the 10 edges is NOT oriented forward along that order.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

from pysat.solvers import Glucose3

N = 13
PAIRS = list(itertools.combinations(range(N), 2))
VIDX = {p: 1 + i for i, p in enumerate(PAIRS)}
FIVES = list(itertools.combinations(range(N), 5))


def var(i, j):
    return VIDX[(i, j)] if i < j else VIDX[(j, i)]


def build_clauses():
    clauses = []
    for S in FIVES:
        for order in itertools.permutations(S):
            # order[0] beats order[1] beats ... beats order[4]
            cl = []
            for a in range(5):
                for b in range(a + 1, 5):
                    u, v = order[a], order[b]   # u is earlier; forward = u -> v
                    if u < v:
                        cl.append(-VIDX[(u, v)])   # not (u->v)
                    else:
                        cl.append(VIDX[(v, u)])    # not (u->v) == (v->u)
            clauses.append(cl)
    return clauses


def verify(beat):
    """Return the number of transitive 5-subsets (0 == success)."""
    bad = 0
    for S in FIVES:
        trans = False
        for order in itertools.permutations(S):
            if all(beat[order[a]][order[b]] for a in range(5) for b in range(a + 1, 5)):
                trans = True
                break
        if trans:
            bad += 1
    return bad


def main() -> int:
    clauses = build_clauses()
    print(f"vars={len(PAIRS)} clauses={len(clauses)}")
    solver = Glucose3()
    for cl in clauses:
        solver.add_clause(cl)
    ok = solver.solve()
    print("SAT:", ok)
    if not ok:
        return 1
    model = set(l for l in solver.get_model() if l > 0)

    beat = [[False] * N for _ in range(N)]
    for (i, j) in PAIRS:
        if VIDX[(i, j)] in model:
            beat[i][j] = True
        else:
            beat[j][i] = True

    bad = verify(beat)
    print("transitive 5-subsets:", bad)

    out = Path(r"E:\新建文件夹2\_tools\tournament13.json")
    adj = {v: [u for u in range(N) if u != v and beat[v][u]] for v in range(N)}
    out.write_text(json.dumps({"n": N, "out_neighbours": adj,
                               "transitive5": bad}, indent=1), encoding="utf-8")
    print("wrote", out)
    print("\nADJACENCY (v: out-neighbours):")
    for v in range(N):
        print(f"  {v:2d} -> {adj[v]}")
    print("\nMACHINE:")
    print(",".join("[" + ";".join(map(str, adj[v])) + "]" for v in range(N)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
