# Methodology

Proofsmith is the *convergent* (subtractive) half of the
[Everest Research Algorithm](https://github.com/everest-an/everest-research-algorithm)
applied to a single, sharply defined target: **get a solved theorem through the
Lean kernel with no gaps.**

> Fork test — "are you building something known, or searching for something unknown?"
> Formalizing a solved theorem is **building something known**: the answer exists,
> only the artifact is missing. That is subtractive mode, not exploratory mode.

## The five steps, applied

**0 · Target (measurable).**
`#print axioms <decl>` returns a subset of `{propext, Classical.choice, Quot.sound}`.
Not "looks formalized" — a measurable predicate.

**1 · Question the requirement.**
Who requires it? *The Prize's `lean-verify` rules* (signed: `TheJustinSunPrize/awards`).
What is the minimum obligation? A complete Lean proof of the *original* problem
statement, on a pinned commit, with a clean build and a clean axiom audit.
Anything beyond that (kernel replay, comparator) is a review *level*, not a
requirement for the mechanical gate.

**2 · Delete.**
Delete the prover role entirely (for pre-solved problems it pays nothing).
Delete any dependency not needed by the target theorem. Delete speculative
definitions — keep the smallest faithful statement. Delete "nice to have" lemmas.

**3 · Simplify.**
Prefer the *shortest faithful* formalization. For a counterexample-type problem,
the whole obligation collapses to verifying two concrete integers
(`JSP-000301`: exhibit `12167`, `12168`; show both powerful, neither square).

**4 · Accelerate the loop.**
The loop is `edit → lake build → axiom audit → verdict`. Measured per generation
in `lineage.jsonl`. Cached mathlib oleans keep a full build at ~15–25 s, so the
feedback loop is short enough to iterate.

**5 · Automate — last, not first.**
Only now is it safe to automate: `driver.py` wires the frozen evaluator to a
lineage ledger and a rollback. Automating an unverified process would just
repeat mistakes faster.

## The RSI loop

```
propose ──▶ evaluate (FROZEN) ──▶ promotion gate ──▶ keep / rollback
   ▲                                   │                    │
   └──────── residue + lineage ◀───────┴────────────────────┘
```

| Rule | Implementation |
| --- | --- |
| Evaluator immutable | `evaluator.py` sha256 pinned in `evaluator.pin`; `driver.py` refuses on mismatch (exit 3) |
| Hold-out sealed | `heldout.json`; sealed targets are never auto-accepted |
| Promotion gate | only `standard_axioms_only` is accepted |
| Rejected rolls back | `git checkout -- .` + residue patch saved |
| Lineage | one JSONL record per generation: parent, hashes, verdict, evidence |
| Failure residue | `residue/<target>-gen<N>.patch` |
| Build/review separation | evaluator never sets `semantic_verdict`; stays `not_determined` |

## Why the kernel is the right judge

The Prize's own words: *"you only need to trust the machine's verification, and
the machine only recognizes logic."* The Lean kernel cannot be argued with,
flattered, or prompt-injected. It is the one evaluator that satisfies the
"immutable judge" rule for free — which is exactly why the formalizer column is
automatable and the prover column is not.
