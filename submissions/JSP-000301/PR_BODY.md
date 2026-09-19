# PR body — JSP-000301 Lean formalization

> Paste this into the PR against `TheJustinSunPrize/awards`, with the catalog
> change in `catalog-diff.md` applied on the branch.

---

## Submission type

- [ ] Mathematical solver information
- [x] Lean proof or formalization author information

## Problem

- Problem ID(s): JSP-000301
- Original problem source and exact location: catalog entry
  `problems/catalog-0301-0400.md#JSP-000301`; solution source
  [Go70] S. W. Golomb, *Powerful numbers*, Amer. Math. Monthly **77**(8) (1970),
  848–852 (see also Erdős problem #365).
- Current entry and proposed change: change `Lean proof` from `No` to `Yes`,
  recording the pinned Lean source and the formalization contributor; set
  `Eligible to claim` to `Yes`. No mathematical result is changed — the catalog's
  own review note (2026-09-13) already records the disproof.
- Related issue, if any: none

## Formal statement

- Accepted mathematical solution and review reference: the JSP-000301 review note
  of 2026-09-13 in the catalog already states the disproof with witness
  `12167 = 23³` and `12168 = 2³ × 3² × 13²`, and observes both lie strictly
  between `110² = 12100` and `111² = 12321`.
- Prior solver candidate record: the current catalog entry credits the solver as
  **Solomon W. Golomb (1970)**. This submission is the formalization only.
- Challenge file / equivalent statement location (pinned to a full commit SHA):
  <https://github.com/everest-an/proofsmith/blob/aa1bcd462981a1d788e4390a4294612271179284/Proofsmith/JSP000301.lean>
- Fully qualified target theorem name: `JSP000301.jsp_000301`
- Statement origin: submitter-proposed statement requiring review. Definitions
  used, both standard and given explicitly in the file:
  `Powerful n := ∀ p : ℕ, p.Prime → p ∣ n → p ^ 2 ∣ n`
  `IsSquare n := ∃ k : ℕ, k * k = n`
- Correspondence to the original problem: the original is the yes/no question
  *"If two consecutive positive integers are powerful, must at least one be a
  perfect square?"*. It is a universal claim over all `n : ℕ` with `0 < n`. The
  Lean target negates exactly that universal claim:
  `¬ (∀ n : ℕ, 0 < n → Powerful n → Powerful (n+1) → IsSquare n ∨ IsSquare (n+1))`.
  A single witness satisfying every hypothesis and violating the conclusion is a
  complete disproof; the witness used is `n = 12167`.
  - `0 < n`: `by norm_num`.
  - `Powerful n`, `Powerful (n+1)`: `powerful_12167`, `powerful_12168`
    (every prime divisor is 2, 3, 13 or 23, and each divides to at least the
    second power).
  - `¬ IsSquare n`, `¬ IsSquare (n+1)`: `not_square_12167`, `not_square_12168`
    (both integers lie strictly between `110²` and `111²`).
  All quantifiers, hypotheses and the conclusion match the original; no case is
  narrowed and no extra assumption is introduced.

## Proof submission

```json
[
  {
    "repository": "https://github.com/everest-an/proofsmith",
    "branch": "main",
    "commit": "aa1bcd462981a1d788e4390a4294612271179284"
  }
]
```

- Submission file or equivalent proof entry (path at the commit above):
  `Proofsmith/JSP000301.lean`
- Fully qualified theorem name providing the complete proof:
  `JSP000301.jsp_000301`
- Connection to the formal statement above: the statement and its complete proof
  are in the same declaration `JSP000301.jsp_000301`; the supporting lemmas
  `powerful_12167`, `powerful_12168`, `not_square_12167`, `not_square_12168` are
  in the same file. There are no `sorry`/`admit` placeholders and no added
  unproved assumptions.

## Reproduction

- Exact Lean version and `lean-toolchain` path: `leanprover/lean4:v4.35.0-rc2`
  (`lean-toolchain` at the repository root).
- Pinned dependency versions: mathlib pinned in `lake-manifest.json` to
  `0acbe13e167f256615da586346deba1c16fd1082`.
- Build instructions (link at the selected commit):
  <https://github.com/everest-an/proofsmith/blob/aa1bcd462981a1d788e4390a4294612271179284/README.md>
- Commands from a clean checkout:
  ```bash
  lake exe cache get
  lake build Proofsmith
  ```
- Command and output for the target theorem's axiom audit:
  ```
  # in a file importing Proofsmith:
  #print axioms JSP000301.jsp_000301
  ```
  Output:
  `'JSP000301.jsp_000301' depends on axioms: [propext, Classical.choice, Quot.sound]`
- Statement-to-proof verification entry: the target declaration itself; no
  separate verification entry is needed.

## Pre-submission Lean verification

- Proof repository and full commit SHA checked locally (matches Proof submission):
  `https://github.com/everest-an/proofsmith` @
  `aa1bcd462981a1d788e4390a4294612271179284`
- Verification date and overall conclusion: **2026-09-20 — 验证通过
  (Verification passed)**.
- Short result summary:
  - Statement correspondence: the Lean target negates exactly the original
    universal question; definitions `Powerful` / `IsSquare` are the standard ones.
  - Full coverage: complete — a single valid counterexample disproves the
    universal claim; every hypothesis of the witness is checked.
  - Actual Lean checks: `lake build Proofsmith` (exit 0), `lake env lean
    Proofsmith/JSP000301.lean` (exit 0), axiom audit (exit 0).
  - Verification levels completed: source inspection, real Lean checks, axiom
    audit. Kernel replay and external comparator were **not** run.
  - Trust dependencies: none beyond the standard Lean axioms
    `propext, Classical.choice, Quot.sound`; no `sorryAx`, no custom axioms, no
    `native_decide`.
- Recommended supporting material:
  - Full verification report:
    <https://github.com/everest-an/proofsmith/blob/aa1bcd462981a1d788e4390a4294612271179284/reports/JSP-000301.md>
  - Target manifest:
    <https://github.com/everest-an/proofsmith/blob/aa1bcd462981a1d788e4390a4294612271179284/pipeline/targets/JSP-000301.json>

## Attribution

- Mathematical solver(s) and contribution: **Solomon W. Golomb** (1970
  counterexample; already credited in the current catalog entry).
- Lean formalization author(s) and contribution: **@everest-an** — wrote the Lean
  statement, the four supporting lemmas and the target theorem, and the
  verification harness.
- Independent verifier(s): none.
- Public authorship evidence: the original proof repository
  <https://github.com/everest-an/proofsmith> is owned by the submitting account
  `@everest-an`; the repository's git history records the formalization commits.

## Submission checklist

- [x] I changed only solver attribution, Lean proof information or supporting
      sources in the relevant catalog.
- [x] I supplied the evidence required for the type of change above.
- [x] Any submitted Lean proof is complete at the specified commit and does not
      depend on `sorry`, `admit` or added unproved assumptions.
- [x] I identified the formal statement and proof entry, explained their
      correspondence to the original problem, and supplied reproduction commands
      and the target theorem's axiom audit.
- [x] I confirm that, before opening this PR, the Lean proof passed my local
      self-check using the bundled `lean-verify` skill at the exact listed commit.
- [x] This PR contains no proof source files, archives, binaries or vendored
      dependencies.
- [x] The Lean reference identifies a commit contained in the named branch.
- [x] I am the contributor using my own GitHub account and original proof
      repository, not registering someone else's proof or a mirror.
