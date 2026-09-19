#!/usr/bin/env python3
"""FROZEN EVALUATOR for the autoformalization pipeline.

RSI rule 1 ("the judge is immutable"): the proposer must never be able to
change the score. This file IS the score. Its sha256 is pinned in
`evaluator.pin` and re-checked on every run by `driver.py`; if the hash
changes, every candidate is refused.

The evaluator is deliberately dumb and mechanical:
  1. pin check        -- toolchain string must match the target spec
  2. build            -- `lake build +<Module>`
  3. source check     -- `lake env lean <source_file>`
  4. axiom audit      -- generate `#print axioms <decl>` and run it
It never edits the submission, never "fixes" a proof, never decides math.

Verdicts:
  standard_axioms_only  -- PASS; only propext / Classical.choice / Quot.sound
  proof_gap             -- FAIL; target (transitively) uses sorryAx
  trust_review_required -- REVIEW; other axioms (native_decide, custom, ...)
  build_failed          -- FAIL; build or source check non-zero
  incomplete            -- ERROR; timeout / unparsable / missing input

Usage:
  python evaluator.py <target.json> --out <dir> [--lake <path>]
Emits a single JSON object on stdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

STANDARD = {"propext", "Classical.choice", "Quot.sound"}
AXIOM_RE = re.compile(r"depends on axioms:\s*\[(.*?)\]", re.S)
NO_AXIOM_RE = re.compile(r"does not depend on any axioms")
SELF = Path(__file__).resolve()


def sha256_file(p: Path) -> str | None:
    if not p.exists():
        return None
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def run(argv: list[str], cwd: Path, timeout: int) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run(argv, cwd=str(cwd), capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout)
        return {"argv": argv, "cwd": str(cwd), "exit_code": p.returncode,
                "stdout": p.stdout, "stderr": p.stderr,
                "seconds": round(time.time() - t0, 3)}
    except subprocess.TimeoutExpired:
        return {"argv": argv, "cwd": str(cwd), "exit_code": None,
                "stdout": "", "stderr": f"TIMEOUT after {timeout}s",
                "seconds": round(time.time() - t0, 3)}
    except Exception as exc:  # noqa: BLE001
        return {"argv": argv, "cwd": str(cwd), "exit_code": None,
                "stdout": "", "stderr": f"EXEC ERROR: {exc}",
                "seconds": round(time.time() - t0, 3)}


def parse_axioms(text: str) -> list[str] | None:
    if NO_AXIOM_RE.search(text):
        return []
    m = AXIOM_RE.search(text)
    if not m:
        return None
    body = m.group(1)
    return [a.strip() for a in body.split(",") if a.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lake", default=str(Path.home() / ".elan" / "bin" / "lake.exe"))
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    spec = json.loads(Path(args.target).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    root = Path(spec["project_root"])
    lake = args.lake
    logs: list[dict] = []

    result: dict = {
        "evaluator": "frozen-evaluator/1",
        "evaluator_sha256": sha256_file(SELF),
        "target": spec["id"],
        "declaration": spec["declaration"],
        "project_root": str(root),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }

    # --- 0. pin check -------------------------------------------------------
    tc_file = root / "lean-toolchain"
    actual_tc = tc_file.read_text(encoding="utf-8").strip() if tc_file.exists() else None
    if actual_tc != spec["toolchain"]:
        result.update(verdict="incomplete", exit_code=2,
                      reason=f"toolchain pin mismatch: file={actual_tc!r} spec={spec['toolchain']!r}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    # --- 1. build -----------------------------------------------------------
    r = run([lake, "build", f"+{spec['module']}"], root, args.timeout)
    logs.append(r)
    (out / "build.log").write_text(r["stdout"] + r["stderr"], encoding="utf-8")
    if r["exit_code"] != 0:
        result.update(verdict="build_failed", exit_code=1,
                      reason="lake build non-zero", log=str(out / "build.log"))
        result["commands"] = [{k: v for k, v in x.items() if k not in ("stdout", "stderr")} for x in logs]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    # --- 2. source check ----------------------------------------------------
    src = root / spec["source_file"]
    r = run([lake, "env", "lean", str(src)], root, args.timeout)
    logs.append(r)
    (out / "source-check.log").write_text(r["stdout"] + r["stderr"], encoding="utf-8")
    if r["exit_code"] != 0:
        result.update(verdict="build_failed", exit_code=1,
                      reason="source check non-zero", log=str(out / "source-check.log"))
        result["commands"] = [{k: v for k, v in x.items() if k not in ("stdout", "stderr")} for x in logs]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    # --- 3. axiom audit -----------------------------------------------------
    audit = out / "AuditTarget.lean"
    audit.write_text(
        f"import {spec['module']}\n"
        "set_option pp.all true\n"
        f"#check @{spec['declaration']}\n"
        "set_option pp.universes false in\n"
        f"#print axioms {spec['declaration']}\n",
        encoding="utf-8")
    r = run([lake, "env", "lean", str(audit)], root, args.timeout)
    logs.append(r)
    (out / "axiom-audit.log").write_text(r["stdout"] + r["stderr"], encoding="utf-8")
    if r["exit_code"] != 0:
        result.update(verdict="incomplete", exit_code=2,
                      reason="axiom audit command failed", log=str(out / "axiom-audit.log"))
        result["commands"] = [{k: v for k, v in x.items() if k not in ("stdout", "stderr")} for x in logs]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    axioms = parse_axioms(r["stdout"] + r["stderr"])
    result["commands"] = [{k: v for k, v in x.items() if k not in ("stdout", "stderr")} for x in logs]
    result["axioms"] = axioms
    result["source_sha256"] = sha256_file(src)

    if axioms is None:
        result.update(verdict="incomplete", exit_code=2,
                      reason="could not parse #print axioms output")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    if "sorryAx" in axioms:
        result.update(verdict="proof_gap", exit_code=1,
                      reason="target transitively depends on sorryAx")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    extra = sorted(set(axioms) - STANDARD)
    if extra:
        result.update(verdict="trust_review_required", exit_code=2,
                      reason=f"non-standard axioms observed: {extra}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    result.update(verdict="standard_axioms_only", exit_code=0,
                  reason="build + source + axiom audit clean")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
