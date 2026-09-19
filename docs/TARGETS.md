# Target roadmap

How Proofsmith picks the next problem, and the current shortlist.

## Selection principle

The prize pays the **formalizer** column, and for problems solved *before*
listing the formalizer column is the only payable one. So the objective is:

> maximise (prize tier × probability of a complete Lean proof) ÷ (formalization cost)

Because per-problem prize amounts are not published (only the 7 Pinnacle problems
at USD 1,000,000 each), the practical lever is **cost**: get many cheap, certain
formalizations through the kernel rather than one speculative expensive one.

### Triage signals

| Signal | Why it matters |
| --- | --- |
| **Statement already formalized** | the only thing missing is the proof — the single biggest shortcut |
| **Refutation shape** | a universal claim killed by one counterexample is the cheapest possible obligation (this is why `JSP-000301` was first) |
| **Finite / construction** | an explicit object to verify beats a general theorem |
| **Area** | elementary number theory / combinatorics formalize far more cheaply than analysis, geometry or set theory |

Triage is mechanical (see the pipeline scripts in the working repo) and is a
**keyword heuristic**, not a feasibility proof. Every shortlisted target still
needs a per-problem check of: (a) is the statement formalizable with current
mathlib, (b) is the recorded resolution a complete proof/disproof, (c) what is
the shortest faithful statement.

## The pool

Of the 1,022-problem bank (as of 2026-09-20):

| Bucket | Count |
| --- | --- |
| total problems | 1,022 |
| open | 668 |
| solved | 354 |
| solved **and** Lean-formalized (eligible to claim) | 66 |
| **solved but not formalized** ← our pool | **287** |

Cost classes inside the pool:

| Class | Count | Meaning |
| --- | --- | --- |
| refutation | 10 | one counterexample/disproof settles it |
| finite | 7 | a concrete finite verification |
| construction | 7 | exhibit an object with stated properties |
| proof | 263 | a general theorem |

Only **one** problem in the pool has a formally recorded *statement*:
`JSP-000288`.

## Status

| Problem | Result | Verdict |
| --- | --- | --- |
| `JSP-000301` | ✅ formalized, `standard_axioms_only` | [report](../reports/JSP-000301.md) · [PR #1959](https://github.com/TheJustinSunPrize/awards/pull/1959) |

## Next batch (ranked)

1. **`JSP-000288`** — *must ratios of consecutive terms in the minimal stably
   complete sequences converge to the golden ratio?* Resolution: counterexample
   (GPT Pro, prompted by Liam Price). **Statement already formalized** → only the
   proof is missing. Cheapest target in the pool.
2. **`JSP-001021`** — *how large a transitive subtournament must every tournament
   contain?* The Erdős–Moser conjecture, **disproved by Reid & Parker (1970)** —
   a classical finite counterexample. Finite graph check.
3. **`JSP-000434`** — random elements of a finite abelian group whose subset sums
   cover it; proposed stronger bound **disproved**. Finite abelian groups.
4. **`JSP-000465`** — Turán extremal problem; **counterexample** for a finite
   family of connected bipartite graphs (internal OpenAI model). Finite graph family.
5. **`JSP-000398`** — uniform distribution of scaled integers in the gaps;
   resolution is a **disproof** (Sc69). Needs the statement built carefully.
6. **`JSP-000788`** — finite colouring / sparse sequence whose subset sums omit a
   colour; **negative answer** (GPT Pro). Ramsey-type.
7. **`JSP-001007`** — integers avoiding about half the residue classes modulo each
   of several primes; **negative answer** (Price & GPT-5.4 Pro).
8. **`JSP-000490`** — colouring countably infinite sets with pairwise intersections
   never of size two; **no uniform colour bound** (GPT-5.4 Pro).
9. **`JSP-001000`** — growth of the measure of a real set with no integer ratio of
   distinct elements; integral criterion (Suan & GPT).
10. **`JSP-000383`** — generating infinitely many primes from a prime set; finite
    existence argument (Mrazović–Kovač; independently Alon).

Each entry still needs the per-problem feasibility check above before work starts.

## Long term

`JSP-000007` — **Poincaré conjecture**, Pinnacle tier, USD 1,000,000, solved by
Perelman, **not formalized**. This is the only Pinnacle problem where the
formalizer column is still open. It is a multi-year formalization effort
(comparable to the Fermat's Last Theorem project), so it is tracked separately
from the batch above.
