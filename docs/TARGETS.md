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
| **No existing public formalization** | the formalizer column goes to the first complete proof; an existing public attempt means the slot may be gone |
| **Statement already formalized** | only the proof is missing — a large shortcut *when* the formalized statement matches the recorded resolution |
| **Refutation shape** | a universal claim killed by one counterexample is the cheapest obligation (why `JSP-000301` was first) |
| **Finite witness** | an explicit small object to check beats a general theorem |
| **Area** | elementary number theory / combinatorics formalize far more cheaply than analysis or geometry |

### ⚠ Triage is a heuristic, not a verdict

The cost classifier is **keyword-based and demonstrably wrong sometimes**. Two
confirmed false positives from the first pass:

- `JSP-000434` was classed *refutation* but is really **Erdős Problem 543**, whose
  resolution (Ma–Tang, arXiv:2602.05768) is an **asymptotic analytic bound over
  `𝔽_p`** — expensive, not a finite counterexample.
- `JSP-000288` was ranked first because its statement is formalized, but a public
  formalization attempt already exists (see below) and the problem has two
  competing readings.

**Every target therefore requires a manual feasibility pass**: (a) does an
existing public Lean proof exist; (b) is the recorded resolution finite /
explicit or asymptotic; (c) does the formalized statement, if any, actually
match the recorded resolution.

## The pool

Of the 1,022-problem bank (as of 2026-09-20):

| Bucket | Count |
| --- | --- |
| total problems | 1,022 |
| open | 668 |
| solved | 354 |
| solved **and** Lean-formalized (eligible to claim) | 66 |
| **solved but not formalized** ← our pool | **287** |

## Status

| Problem | Result | Verdict |
| --- | --- | --- |
| `JSP-000301` | ✅ formalized, `standard_axioms_only` | [report](../reports/JSP-000301.md) · [PR #1959](https://github.com/TheJustinSunPrize/awards/pull/1959) |

## Candidate assessments

### `JSP-001021` — Erdős Problem 1216 *(demoted after inspection)*

*How large a transitive subtournament must every tournament of prescribed order
contain?* Erdős–Moser conjectured `f(n) = ⌊log₂ n⌋ + 1`; Reid & Parker (1970)
disproved it.

**The counterexample half is cheap and is done.** A tournament on 13 vertices
with no transitive subtournament of order 5 was computed with a SAT encoding and
verified (`experiments/tournament13.json`, generator `tools/sat_tournament.py`):
every vertex has out-degree 6 and all `C(13,5) = 1287` five-subsets span a
directed triangle.

**The result is not complete without the matching bound**, and that is the
expensive half: the disproof needs `R(5) = 14`, i.e. *every* tournament on 14
vertices has a transitive subtournament of order 5. That is a finite-exhaustive
statement over `2^91` tournaments; it is not a small check and not obviously
formalizable from current mathlib. Verdict: **not a cheap target.**

### ⚠ Lesson learned (recorded so it is not repeated)

**"Refutation-shaped" does not mean cheap.** A refutation of a universal claim
usually also needs the *matching upper bound* to resolve the problem as stated,
and that bound can be the expensive part — exactly what happened here. A cheap
target must have its **entire recorded resolution** be a small finite
verification, not just its witness. Both `JSP-001021` and `JSP-000434` failed
this test after the first pass had promoted them.

### `JSP-000288` — Erdős Problem 346 *(demoted)*

Golden-ratio ratio limit for minimal stably complete sequences.

- Statement **is** formalized (`formal-conjectures/ErdosProblems/346.lean`), but
  the problem has two readings (does convergence *follow*, or is a limit
  *assumed*?) and the recorded resolution is a **counterexample**.
- A public formalization of the "limit-exists" reading already exists:
  `KitaKen1/erdos346-ratio-limit-lean` (sorry-free), imported into
  `Vilin97/lean-pool` via PR #197. **Priority risk.**
- Verdict: only worth attempting if we can show the *counterexample* reading is
  the one JSP-000288 means, and that the existing proof does not already cover it.

### `JSP-000434` — Erdős Problem 543 *(demoted)*

- Resolution is an **asymptotic lower bound** `f(p) ≥ log₂p + (1/(2log2)+o(1))loglog p`
  (Ma & Tang). Not a finite counterexample; expensive to formalize.

### Other refutation-shaped entries (unverified)

`JSP-000465` (Turán counterexample, internal OpenAI model), `JSP-000398`
(uniform-distribution disproof, Sc69), `JSP-000788` (Ramsey negative answer),
`JSP-001007` (residue-class negative answer), `JSP-000490` (no uniform colour
bound), `JSP-001000`, `JSP-000383`. Each needs the same manual pass.

## Long term

`JSP-000007` — **Poincaré conjecture**, Pinnacle tier, USD 1,000,000, solved by
Perelman, **not formalized**. The only Pinnacle problem where the formalizer
column is still open. A multi-year effort, tracked separately.
