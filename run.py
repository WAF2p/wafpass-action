#!/usr/bin/env python3
"""GitHub Action runner for WOMBATpass.

Installs the wombat CLI if needed, runs the scan, pushes the JSON result to the
Wombat server /api/v1/runs endpoint, and fails the step according to the configured policy.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    """Read a WOMBAT_* setting, falling back to the deprecated WAFPASS_* name."""
    value = os.environ.get(name)
    if value is None and name.startswith("WOMBAT_"):
        legacy = "WAFPASS_" + name[len("WOMBAT_"):]
        value = os.environ.get(legacy)
        if value is not None:
            print(
                f"WARNING: {legacy} is deprecated; use {name} instead.",
                file=sys.stderr,
            )
    return (value if value is not None else default).strip()


def _split_paths(raw: str) -> list[str]:
    """Split scan_path input into separate path arguments.

    Supports space-separated paths while respecting simple shell quoting,
    so callers can pass './aws ./azure' or '"./path with spaces"'.
    """
    if not raw:
        return ["."]
    return shlex.split(raw)


def _ensure_wombat() -> str:
    """Return the absolute path to the wombat executable, installing if needed.

    Falls back to a pre-installed legacy ``wafpass`` binary during the rebrand
    migration window.
    """
    try:
        return subprocess.check_output(["which", "wombat"], text=True).strip()
    except subprocess.CalledProcessError:
        pass

    try:
        legacy = subprocess.check_output(["which", "wafpass"], text=True).strip()
        print(
            "WARNING: the 'wafpass' command is deprecated; install 'wombat-core' instead.",
            file=sys.stderr,
        )
        return legacy
    except subprocess.CalledProcessError:
        pass

    source = _env("WOMBAT_SOURCE")
    version = _env("WOMBAT_VERSION")

    if source:
        package = source
    else:
        package = "wombat-core"
        if version:
            package = f"{package}=={version}"

    print(f"Installing {package}...", file=sys.stderr)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError:
        # Migration fallback: the new package may not be published yet.
        legacy_package = "wafpass-core"
        if version:
            legacy_package = f"{legacy_package}=={version}"
        print(
            f"WARNING: {package} could not be installed; falling back to "
            f"deprecated {legacy_package}.",
            file=sys.stderr,
        )
        subprocess.check_call([sys.executable, "-m", "pip", "install", legacy_package])

    try:
        return subprocess.check_output(["which", "wombat"], text=True).strip()
    except subprocess.CalledProcessError:
        return subprocess.check_output(["which", "wafpass"], text=True).strip()


def _build_args() -> list[str]:
    args: list[str] = ["--output", "json", "--iac", _env("WOMBAT_IAC", "terraform").lower()]

    project = _env("WOMBAT_PROJECT") or _env("GITHUB_REPOSITORY")
    if project:
        args.extend(["--project", project])

    branch = _env("WOMBAT_BRANCH") or _env("GITHUB_REF_NAME")
    if branch:
        args.extend(["--branch", branch])

    git_sha = _env("WOMBAT_GIT_SHA") or _env("GITHUB_SHA")
    if git_sha:
        args.extend(["--git-sha", git_sha])

    args.extend(["--triggered-by", "github-actions", "--is-cicd"])

    stage = _env("WOMBAT_STAGE")
    if stage:
        args.extend(["--stage", stage])

    severity = _env("WOMBAT_MIN_SEVERITY")
    if severity:
        args.extend(["--severity", severity])

    push_url = _env("WOMBAT_PUSH_URL")
    server_controls = _env("WOMBAT_SERVER_CONTROLS", "false").lower() == "true"
    controls_dir = _env("WOMBAT_CONTROLS_DIR")

    if server_controls:
        if not push_url:
            print("ERROR: server_controls=true requires server_url", file=sys.stderr)
            sys.exit(2)
        args.extend(["--server-url", push_url])
    elif controls_dir:
        args.extend(["--controls-dir", controls_dir])

    if _env("WOMBAT_VERBOSE", "false").lower() == "true":
        args.append("--verbose")

    plan_file = _env("WOMBAT_PLAN_FILE")
    if plan_file:
        args.extend(["--plan-file", plan_file])

    if _env("WOMBAT_UPLOAD_SOURCE", "false").lower() == "true":
        args.append("--upload-source")

    return args


def _run_scan(wombat: str) -> dict:
    paths = _split_paths(_env("WOMBAT_SCAN_PATH", "."))
    cmd = [wombat, "check", *paths, *_build_args()]

    print(f"Running: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode not in (0, 1):
        # 0 = success, 1 = failures found (CLI default --fail-on fail); 2+ = error
        print(result.stderr, file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        sys.exit(2)

    output = result.stdout
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        pass

    # The CLI may emit log lines before/after the JSON object; search for it.
    start = output.find("{")
    if start == -1:
        print("ERROR: No JSON result found in wombat output", file=sys.stderr)
        print(output, file=sys.stderr)
        sys.exit(2)

    try:
        return json.loads(output[start:])
    except json.JSONDecodeError as exc:
        print(f"ERROR: Failed to parse JSON result: {exc}", file=sys.stderr)
        print(output, file=sys.stderr)
        sys.exit(2)


def _push_result(payload: dict) -> dict:
    import httpx

    push_url = _env("WOMBAT_PUSH_URL").rstrip("/")
    url = f"{push_url}/api/v1/runs"

    token = _env("WOMBAT_API_TOKEN")
    api_key = _env("WOMBAT_API_KEY")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key
    elif token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        print("ERROR: Either api_token or api_key must be provided", file=sys.stderr)
        sys.exit(2)

    print(f"Pushing result to {url}...", file=sys.stderr)
    resp = httpx.post(url, json=payload, headers=headers, timeout=120)
    print(f"Server responded: HTTP {resp.status_code}", file=sys.stderr)
    if resp.status_code >= 400:
        print(resp.text, file=sys.stderr)
        sys.exit(2)

    try:
        return resp.json()
    except json.JSONDecodeError:
        print("WARNING: Server did not return JSON", file=sys.stderr)
        return {}


def _set_output(name: str, value: str) -> None:
    output_file = _env("GITHUB_OUTPUT")
    if not output_file:
        return
    with open(output_file, "a") as f:
        f.write(f"{name}={value}\n")


def _severity_rank(severity: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(severity.lower(), 0)


def _apply_fail_on(payload: dict) -> None:
    fail_on = _env("WOMBAT_FAIL_ON", "fail").lower()
    if fail_on == "never":
        return

    findings = payload.get("findings", [])
    total_fail = sum(1 for f in findings if f.get("status") == "FAIL")
    total_skip = sum(1 for f in findings if f.get("status") == "SKIP")

    if fail_on == "fail" and total_fail > 0:
        print(f"Failing step: {total_fail} failing finding(s)", file=sys.stderr)
        sys.exit(1)
    if fail_on in ("skip", "any") and (total_fail > 0 or total_skip > 0):
        print(
            f"Failing step: {total_fail} failing, {total_skip} skipped finding(s)",
            file=sys.stderr,
        )
        sys.exit(1)
    if fail_on in ("low", "medium", "high", "critical"):
        threshold = _severity_rank(fail_on)
        for f in findings:
            if _severity_rank(f.get("severity", "")) >= threshold:
                print(
                    f"Failing step: found {f.get('severity')} severity finding {f.get('check_id')}",
                    file=sys.stderr,
                )
                sys.exit(1)


def main() -> None:
    wombat = _ensure_wombat()
    payload = _run_scan(wombat)
    response = _push_result(payload)

    data = response.get("data", {})
    run_id = data.get("id", "")
    score = data.get("score", "")
    findings_count = len(payload.get("findings", []))

    _set_output("run_id", str(run_id))
    _set_output("score", str(score))
    _set_output("findings_count", str(findings_count))

    print(f"run_id={run_id}")
    print(f"score={score}")
    print(f"findings_count={findings_count}")

    _apply_fail_on(payload)


if __name__ == "__main__":
    main()
