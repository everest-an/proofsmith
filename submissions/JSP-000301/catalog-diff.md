# Catalog change — JSP-000301

File: `problems/catalog-0301-0400.md`
Section: `<a id="JSP-000301"></a>`

## Before

```
| Current status | Solved<br>Proof contributors: Solomon W. Golomb (counterexample in [Go70], 1970; [attribution source](https://www.erdosproblems.com/latex/365)). |
| Lean proof | No |
| Eligible to claim | No |
```

## After

```
| Current status | Solved<br>Proof contributors: Solomon W. Golomb (counterexample in [Go70], 1970; [attribution source](https://www.erdosproblems.com/latex/365)). |
| Lean proof | Yes — [Lean source](https://github.com/everest-an/proofsmith/blob/aa1bcd462981a1d788e4390a4294612271179284/Proofsmith/JSP000301.lean)<br>Formalization contributors: @everest-an. |
| Eligible to claim | Yes |
```

## Rationale

- `Lean proof` follows the same display convention as other `Yes` entries
  (e.g. JSP-000005): a commit-pinned source link plus a
  `Formalization contributors:` credit.
- `Eligible to claim` moves to `Yes` because the problem now has a complete Lean
  proof (`problems/README.md`: *"When a problem is fully solved, has a Lean
  formal proof, and becomes eligible to claim, update Claim status …"*).
- No change is made to the mathematical record; the solver credit is untouched.
- The corresponding index row in `problems/README.md` for JSP-000301
  (`Lean proof` `No → Yes`, `Eligible to claim` `No → Yes`) is left to maintainers
  if they prefer to regenerate it, or may be updated in the same PR.
