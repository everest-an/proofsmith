#!/usr/bin/env python3
"""Autoformalization loop driver.

Implements the RSI loop from the Everest Research Algorithm (divergent mode):
    propose -> evaluate (FROZEN evaluator) -> promotion gate -> keep / rollback
            -> record lineage -> next generation

Hard rules enforced here:
  * R1 judge immutable : evaluator.py sha256 must equal evaluator.pin; else refuse.
  * R2 held-out sealed : targets in heldout.json are never auto-accepted by this
                         driver; they require the separate review step.
  * R3 gate or nothing : a candidate is only "accepted" on verdict
                         standard_axioms_only.
  * R4 rejected rolls  : on any other verdict the project tree is restored to the
    back cleanly        last accepted commit, and the rejected diff is kept as
                         structured residue for the next round.
  * R5 lineage         : every generation appends one JSONL record with parent,
                         hashes, verdict and evidence paths.
  * R6 residue         : failure diffs land in residue/ and are referenced by the
                         lineage record.
  * R7 build/review    : the evaluator only speaks mechanically; the semantic
    separation          statement-correspondence verdict is a separate reviewer
                         step and is never set by this driver.

Usage:
  python driver.py run    <target.json> [--note "what changed this generation"]
  python driver.py status [--target JSP-000301]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVALUATOR = HERE / "evaluator.py"
PIN = HERE / "evaluator.pin"
LEDGER = HERE / "lineage.jsonl"
RESIDUE = HERE / "residue"
HELDOUT = HERE / "heldout.json"
LAKE = str(Path.home() / ".elan" / "bin" / "lake.exe")
PASS = "standard_axioms_only"


def sha256_file(p: Path) -> str | None:
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=str(root), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr).strip()


def check_evaluator() -> str:
    """R1: refuse to run if the judge changed since it was pinned."""
    cur = sha256_file(EVALUATOR)
    if not PIN.exists():
        PIN.write_text(cur or "", encoding="utf-8")
        return cur or ""
    pinned = PIN.read_text(encoding="utf-8").strip()
    if cur != pinned:
        print(f"REFUSED: evaluator.py changed (pin={pinned[:12]}… now={str(cur)[:12]}…).\n"
              f"         The judge must be immutable. Re-pin deliberately if intended.",
              file=sys.stderr)
        sys.exit(3)
    return cur


def load_ledger() -> list[dict]:
    if not LEDGER.exists():
        return []
    return [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]


def append_ledger(rec: dict) -> None:
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def cmd_run(args) -> int:
    ev_sha = check_evaluator()
    spec = json.loads(Path(args.target).read_text(encoding="utf-8"))
    tid = spec["id"]
    root = Path(spec["project_root"])

    heldout = json.loads(HELDOUT.read_text(encoding="utf-8")) if HELDOUT.exists() else {"sealed": []}
    sealed = tid in heldout.get("sealed", [])

    ledger = load_ledger()
    gen = len([r for r in ledger if r["target"] == tid]) + 1
    parent = next((r["generation"] for r in reversed(ledger)
                   if r["target"] == tid and r["verdict"] == PASS), None)

    # snapshot BEFORE evaluation
    head = git(root, "rev-parse", "HEAD")[1]
    dirty = git(root, "status", "--porcelain")[1]

    out = HERE / "runs" / f"{tid}-gen{gen}"
    out.mkdir(parents=True, exist_ok=True)
    print(f"[gen {gen}] target={tid} evaluator={ev_sha[:12]}… head={head[:12]}…")
    if dirty:
        print(f"[gen {gen}] working tree dirty before eval:\n{dirty}")

    # --- evaluate (frozen gate) ---
    proc = subprocess.run([sys.executable, str(EVALUATOR), str(args.target),
                           "--out", str(out), "--lake", LAKE],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        verdict = json.loads(proc.stdout)
    except json.JSONDecodeError:
        verdict = {"verdict": "incomplete", "exit_code": 2,
                   "reason": f"evaluator produced no JSON: {proc.stderr[:400]}"}
    v = verdict.get("verdict", "incomplete")
    passed = (v == PASS) and not sealed

    # --- R4/R6: rollback + residue on rejection ---
    residue_path = None
    if not passed:
        RESIDUE.mkdir(exist_ok=True)
        _, diff = git(root, "diff", "HEAD")
        _, untracked = git(root, "status", "--porcelain")
        residue_path = RESIDUE / f"{tid}-gen{gen}.patch"
        residue_path.write_text(
            f"# rejected candidate residue  target={tid} gen={gen} verdict={v}\n"
            f"# reason: {verdict.get('reason')}\n"
            f"# --- git status ---\n{untracked}\n# --- git diff HEAD ---\n{diff}\n",
            encoding="utf-8")
        git(root, "checkout", "--", ".")
        git(root, "clean", "-fd", "--", "*.lean")  # only stray proof files
        print(f"[gen {gen}] REJECTED ({v}): {verdict.get('reason')}")
        print(f"[gen {gen}] rolled back to HEAD; residue -> {residue_path}")
    else:
        print(f"[gen {gen}] ACCEPTED ({v}); axioms={verdict.get('axioms')}")

    rec = {
        "target": tid,
        "generation": gen,
        "parent_accepted": parent,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "proposer_note": args.note or "",
        "verdict": v,
        "accepted": passed,
        "sealed_holdout": sealed,
        "reason": verdict.get("reason"),
        "axioms": verdict.get("axioms"),
        "source_sha256": verdict.get("source_sha256"),
        "evaluator_sha256": ev_sha,
        "project_head_before": head,
        "residue": str(residue_path) if residue_path else None,
        "evidence_dir": str(out),
        "semantic_verdict": "not_determined",  # R7: never set by this driver
    }
    append_ledger(rec)
    print(f"[gen {gen}] lineage appended -> {LEDGER}")
    return 0 if passed else 1


def cmd_status(args) -> int:
    ledger = load_ledger()
    rows = [r for r in ledger if not args.target or r["target"] == args.target]
    if not rows:
        print("(no lineage records)")
        return 0
    print(f"{'target':<14}{'gen':<5}{'verdict':<24}{'ok':<4}{'axioms'}")
    for r in rows:
        print(f"{r['target']:<14}{r['generation']:<5}{r['verdict']:<24}"
              f"{str(r['accepted']):<4}{r.get('axioms')}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("target")
    r.add_argument("--note", default="")
    s = sub.add_parser("status")
    s.add_argument("--target", default=None)
    args = ap.parse_args()
    return cmd_run(args) if args.cmd == "run" else cmd_status(args)


if __name__ == "__main__":
    sys.exit(main())
