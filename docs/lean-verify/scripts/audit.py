#!/usr/bin/env python3
"""Target-scoped Lean audit. A mechanical result is never a mathematical verdict.

Python 3.9+, standard library only. Run `run` INSIDE an already isolated,
prepared project. This program is not a sandbox or an independent checker.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
NAME = re.compile(r"[^\W\d]\w*'*(?:\.[^\W\d]\w*'*)*\Z", re.UNICODE)
ID = re.compile(r"[A-Za-z0-9_-]+\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_field(obj, key):
    value = obj.get(key)
    require(isinstance(value, str) and bool(value.strip()), f"missing/invalid {key}")
    return value


def unique(items, label):
    require(isinstance(items, list) and items, f"{label} must be a nonempty list")
    result = {}
    for item in items:
        require(isinstance(item, dict), f"invalid {label} entry")
        key = text_field(item, "id")
        require(ID.fullmatch(key) and key not in result, f"duplicate/invalid {label} id: {key}")
        result[key] = item
    return result


def load_manifest(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), "manifest must be a JSON object")
    require(data.get("schema_version") == 1, "unsupported schema_version")
    project = data.get("project", {})
    require(isinstance(project, dict), "project must be a JSON object")
    root = Path(text_field(project, "root"))
    require(root.is_absolute() and root.is_dir(), "project.root must be an existing absolute directory")
    root = root.resolve()
    require(re.fullmatch(r"[0-9a-f]{40}", text_field(project, "commit")), "commit must be a full lowercase SHA")
    text_field(project, "repository")
    text_field(project, "toolchain")
    problems = unique(data.get("problems"), "problems")
    targets = unique(data.get("targets"), "targets")
    declarations = set()
    for target in targets.values():
        require(target.get("problem") in problems, "target references unknown problem")
        require(target.get("role") in {"theorem", "bridge"}, "invalid target role")
        for field in ("module", "declaration"):
            require(NAME.fullmatch(text_field(target, field)), f"unsupported Lean {field}; use a reviewed harness for escaped identifiers")
        require(target["declaration"] not in declarations, "duplicate declaration")
        declarations.add(target["declaration"])
        source = Path(text_field(target, "source"))
        require(not source.is_absolute() and ".." not in source.parts and source.suffix == ".lean", "source must be a relative .lean path")
        require((root / source).resolve().is_relative_to(root), "source escapes project root")
    covered = set()
    for problem in problems.values():
        text_field(problem, "source")
        for req in unique(problem.get("requirements"), "requirements").values():
            text_field(req, "description")
            refs = req.get("targets")
            require(isinstance(refs, list) and len(refs) == len(set(refs)), "invalid requirement targets")
            require(req.get("coverage") in {"pending", "full", "partial", "uncovered"}, "invalid coverage")
            if not refs:
                require(req["coverage"] == "uncovered", "empty targets must be marked uncovered")
            for ref in refs:
                require(ref in targets and targets[ref]["problem"] == problem["id"], "unknown/cross-problem target")
            if req["coverage"] != "pending":
                text_field(req, "evidence")
            covered.update(refs)
    require(covered == set(targets), "every target must be linked to a requirement")
    return data, root


def audit_source(target):
    # Names are validated; there is no user-controlled Lean fragment here.
    name = target["declaration"]
    return (f"import {target['module']}\n\nset_option pp.all true\n"
            f"#check @{name}\n#print {name}\n"
            f"set_option pp.universes false in\n#print axioms {name}\n")


def parse_axioms(output, declaration):
    pattern = (r"^'" + re.escape(declaration) +
               r"' (?:does not depend on any axioms|depends on axioms:\s*\[([^\]]*)\])\s*$")
    matches = list(re.finditer(pattern, output, re.MULTILINE))
    require(len(matches) == 1, "missing, duplicate, or unsupported axiom output")
    body = matches[0].group(1)
    if body is None or not body.strip():
        return []
    axioms = [name.strip() for name in body.split(",")]
    require(all(NAME.fullmatch(name) for name in axioms), "unsupported axiom name/output")
    require(len(axioms) == len(set(axioms)), "duplicate axiom names")
    return axioms


def classify(axioms):
    if "sorryAx" in axioms:
        return "proof_gap"
    if set(axioms) - STANDARD_AXIOMS:
        return "trust_review_required"
    return "standard_axioms_only"


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def capture(argv, cwd, log, timeout):
    started = time.monotonic()
    result = {"argv": list(map(str, argv)), "cwd": str(cwd), "log": str(log), "exit_code": None}
    env = dict(os.environ)
    # Lake reconstructs these inside the prepared, isolated project.
    env.pop("LEAN_PATH", None)
    env.pop("LEAN_SRC_PATH", None)
    with log.open("wb") as stream:
        try:
            proc = subprocess.Popen(result["argv"], cwd=cwd, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, start_new_session=True)
            try:
                result["exit_code"] = proc.wait(timeout=timeout)
                result["status"] = "ok" if proc.returncode == 0 else "command_failed"
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                result["exit_code"] = proc.returncode
                result["status"] = "timeout"
            except BaseException:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                raise
        except OSError as exc:
            result["status"] = "launch_failed"
            result["error"] = str(exc)
    result["seconds"] = round(time.monotonic() - started, 3)
    result["log_sha256"] = digest(log)
    return result


def git_bytes(root, *args):
    # No hooks or external fsmonitor. Never fetches or mutates the checkout.
    return subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                           "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
                          capture_output=True, timeout=20, check=True).stdout


def git_read(root, *args):
    return git_bytes(root, *args).decode("utf-8").strip()


def snapshot(root, data):
    files = {"lean-toolchain", "lakefile.lean", "lakefile.toml", "lake-manifest.json"}
    files.update(t["source"] for t in data["targets"])
    return {name: digest(root / name) if (root / name).is_file() else None for name in sorted(files)}


def preflight(data, root):
    root = root.resolve()
    issues = []
    hashes = snapshot(root, data)
    expected = data["project"]
    toolchain = (root / "lean-toolchain").read_text().strip() if hashes["lean-toolchain"] else None
    if toolchain != expected["toolchain"]:
        issues.append("toolchain_file_mismatch_or_missing")
    if not (hashes["lakefile.lean"] or hashes["lakefile.toml"]):
        issues.append("lake_config_missing")
    if not hashes["lake-manifest.json"]:
        issues.append("dependency_lock_missing")
    for target in data["targets"]:
        if hashes[target["source"]] is None:
            issues.append("source_missing:" + target["id"])
    try:
        head = git_read(root, "rev-parse", "HEAD")
        state = git_read(root, "status", "--porcelain", "--untracked-files=all")
        if head != expected["commit"]:
            issues.append("commit_mismatch")
        # --untracked-files=all may contain independently authored bridge files.
        if any(line[:2] != "??" for line in state.splitlines()):
            issues.append("tracked_worktree_changes")
        repo_root = Path(git_read(root, "rev-parse", "--show-toplevel")).resolve()
        for target in data["targets"]:
            if target["role"] == "theorem":
                relative = (root / target["source"]).relative_to(repo_root).as_posix()
                try:
                    blob = git_bytes(root, "cat-file", "blob", expected["commit"] + ":" + relative)
                    if hashlib.sha256(blob).hexdigest() != hashes[target["source"]]:
                        issues.append("source_differs_from_commit:" + target["id"])
                except subprocess.CalledProcessError:
                    issues.append("source_not_in_commit:" + target["id"])
    except (OSError, subprocess.SubprocessError) as exc:
        head, state = None, None
        issues.append("git_snapshot_unavailable:" + str(exc))
    return {"ready_for_target_checks": not issues, "issues": issues, "head": head,
            "git_status": state, "toolchain_file": toolchain, "file_sha256": hashes,
            "manual_preconditions": ["isolation and resource limits established",
                                     "clean source build and trusted cache provenance recorded",
                                     "actual dependency SHAs match fixed evidence",
                                     "tool binaries are trusted and match the pinned toolchain",
                                     "all untracked inputs and module/source mappings reviewed"],
            "checker_compatibility": "not_probed; inspect pinned checker separately"}


def execute(data, root, out, lake, timeout):
    before = preflight(data, root)
    result = {"scope": "target_checks_only", "semantic_verdict": "not_determined",
              "preflight": before, "commands": [], "targets": [], "mechanical_status": "incomplete"}
    if not before["ready_for_target_checks"]:
        return result, 2
    version_records = []
    for index, command in enumerate(([lake, "--version"], [lake, "env", "lean", "--version"])):
        record = capture(command, root, out / f"version-{index}.log", timeout)
        version_records.append(record)
        result["commands"].append(record)
        if record["status"] != "ok":
            result["reason"] = "tool_version_check_failed"
            return result, 2
    result["tool_versions"] = [Path(r["log"]).read_text(encoding="utf-8") for r in version_records]
    release = re.fullmatch(r"leanprover/lean4:v(\d+\.\d+\.\d+(?:-rc\d+)?)", data["project"]["toolchain"])
    observed = re.search(r"Lean \(version ([^,\s]+)", result["tool_versions"][1])
    if not release or not observed or release[1] != observed[1]:
        result["reason"] = "tool_version_mismatch_or_unsupported_pin; manual verification required"
        return result, 2
    for index, target in enumerate(data["targets"]):
        audit = out / f"Audit{index:04d}.lean"
        audit.write_text(audit_source(target), encoding="utf-8")
        row = {"id": target["id"], "declaration": target["declaration"],
               "audit_file": str(audit), "audit_sha256": digest(audit), "status": "incomplete"}
        result["targets"].append(row)
        # Explicit module build prevents default-target omissions. The caller must
        # already have done a clean build; this incremental command is not one.
        commands = [[lake, "build", "+" + target["module"]],
                    [lake, "env", "lean", str(root / target["source"])],
                    [lake, "env", "lean", str(audit)]]
        records = []
        for step, command in enumerate(commands):
            record = capture(command, root, out / f"{index:04d}-{step}.log", timeout)
            records.append(record)
            result["commands"].append(record)
            if record["status"] != "ok":
                row["reason"] = record["status"]
                break
        else:
            try:
                axioms = parse_axioms(Path(records[-1]["log"]).read_text(encoding="utf-8"), target["declaration"])
                row.update(axioms=axioms, status=classify(axioms))
            except (ValueError, UnicodeError) as exc:
                row["reason"] = str(exc)
        row["commands"] = records
    after = preflight(data, root)
    result["after"] = after
    # Ignore newly generated untracked build artifacts; preserve both status logs.
    stable = (before["file_sha256"] == after["file_sha256"] and
              before["head"] == after["head"] and after["ready_for_target_checks"])
    result["inputs_stable"] = stable
    statuses = {r["status"] for r in result["targets"]}
    if not stable:
        return result, 2
    if "proof_gap" in statuses:
        result["mechanical_status"] = "proof_gap"
        return result, 1
    if "incomplete" in statuses:
        return result, 2
    if "trust_review_required" in statuses:
        result["mechanical_status"] = "trust_review_required"
        return result, 2
    result["mechanical_status"] = "standard_axioms_only"
    return result, 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["preflight", "prepare", "run"])
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="new directory outside the project")
    parser.add_argument("--lake", type=Path, help="absolute trusted Lake binary (run only)")
    parser.add_argument("--timeout", type=float, default=300, help="seconds per command")
    args = parser.parse_args(argv)
    try:
        require(args.timeout > 0 and args.timeout < float("inf"), "timeout must be finite and positive")
        data, root = load_manifest(args.manifest)
        out = args.out.resolve()
        require(not out.is_relative_to(root) and not root.is_relative_to(out), "output and project must be separate directories")
        require(not args.out.exists(), "output already exists; use a fresh directory")
        if args.action == "run":
            require(args.lake is not None and args.lake.is_absolute() and args.lake.is_file(), "run requires an absolute trusted --lake binary")
        out.mkdir(parents=True)
        save_json(out / "manifest.json", data)
        if args.action == "run":
            result, code = execute(data, root, out, str(args.lake), args.timeout)
        else:
            result = preflight(data, root)
            if args.action == "prepare":
                for index, target in enumerate(data["targets"]):
                    (out / f"Audit{index:04d}.lean").write_text(audit_source(target), encoding="utf-8")
            code = 0 if result["ready_for_target_checks"] else 2
        result["manifest_sha256"] = digest(out / "manifest.json")
        result["script_sha256"] = digest(Path(__file__))
        result["exit_code"] = code
        save_json(out / "result.json", result)
        print(out / "result.json")
        return code
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"audit incomplete: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
