# Proofsmith

**Machine-verified formalizations of solved mathematics — one Lean proof at a time.**

Proofsmith turns *already-proven* theorems into kernel-checked Lean 4 proofs and
submits them to the **formalization column** of [The Justin Sun Prize](https://www.hejustinsun.com/prize).

> *Quod probatur, solvitur* — "proved, then paid".

---

## Why this exists

The Justin Sun Prize splits each problem into two credited roles:

| Role | Share | What it means |
| --- | --- | --- |
| **Prover** | 70 % | first to produce a complete solution |
| **Formalizer** | 30 % | first to make that solution machine-checkable in Lean |

For problems that were **already solved before they were listed** — which is most
of the ~350 solved entries in the [1,022-problem bank](https://github.com/TheJustinSunPrize/awards/tree/main/problems) —
the prover column pays nothing and **the money goes to whoever formalizes it**.

That is the whole bet: the mathematics already exists, the bottleneck is
*engineering*, and engineering is what can be automated. Proofsmith is the
factory.

## Status

| Problem | Statement | Witness / method | Verdict | Report |
| --- | --- | --- | --- | --- |
| `JSP-000301` | consecutive powerful numbers, at least one a square? | Golomb counterexample `12167 = 23³`, `12168 = 2³·3²·13²` | ✅ `standard_axioms_only` | [report](reports/JSP-000301.md) |

## Repository layout

```
Proofsmith/            Lean 4 library — one module per JSP problem
Proofsmith.lean        library root (imports every module)
pipeline/
  evaluator.py         FROZEN evaluator — the promotion gate (do not edit mid-run)
  driver.py            RSI loop: propose -> gate -> keep/rollback -> lineage
  targets/*.json       per-problem specs consumed by the evaluator
  heldout.json         sealed hold-out set (never auto-accepted)
reports/               one verification report per formalized problem
docs/
  METHODOLOGY.md       how the loop works, mapped to the RSI rules
  TARGETS.md           how targets are picked + the current ranked shortlist
  lean-verify/         a copy of the Prize's own pre-submission audit skill
```

## Reproduce

```bash
# toolchain (matches mathlib master)
cat lean-toolchain                     # leanprover/lean4:v4.35.0-rc2

# build the library
lake exe cache get                     # fetch mathlib's prebuilt oleans
lake build Proofsmith

# run the frozen gate on a target
python pipeline/evaluator.py pipeline/targets/JSP-000301.json --out /tmp/out --lake "$(which lake)"
# -> verdict: standard_axioms_only, axioms [propext, Classical.choice, Quot.sound]

# run the full loop (gate + lineage + rollback on failure)
python pipeline/driver.py run pipeline/targets/JSP-000301.json --note "..."
python pipeline/driver.py status
```

A proof is **only** accepted when the kernel agrees and the transitive axiom
list is at most `propext, Classical.choice, Quot.sound`. Anything else —
`sorryAx`, custom axioms, `native_decide` — is rejected and rolled back.

## Design rules

The pipeline follows the RSI (recursive self-improvement) discipline from the
[Everest Research Algorithm](https://github.com/everest-an/everest-research-algorithm):

1. **The judge is immutable.** `evaluator.py` is hashed and pinned; if it changes,
   every candidate is refused.
2. **The hold-out set is sealed.** Problems in `heldout.json` are never auto-accepted.
3. **No gate, no improvement.** "It looks better" is not evidence; only a passing
   kernel check counts.
4. **Rejected work rolls back cleanly.** The tree is restored to the last accepted
   commit; the rejected diff is kept as structured residue.
5. **Every generation records lineage.** Parent, hashes, verdict, evidence.
6. **Failures feed the next round.** Residue is a curriculum, not noise.
7. **Build and review are separated.** The evaluator is purely mechanical; the
   semantic statement-correspondence verdict is always `not_determined` from it
   and must be set by a separate human/model review.

## License

MIT — see [LICENSE](LICENSE). Proof *content* follows the terms of the Prize's
`LICENSE-CONTENT`.
