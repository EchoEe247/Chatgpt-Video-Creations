from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "workflow" / "CURRENT.json"
LANES = {"auto", "cinematic", "animation", "business"}




def _version_tuple(value: str) -> tuple[int, ...]:
    parts = [int(x) for x in re.findall(r"\d+", str(value or ""))]
    return tuple(parts or [0])


def query_live_bridge_status(url: str | None = None, *, timeout: float = 3.0) -> dict[str, Any]:
    endpoint = url or os.environ.get("HERMES_MCP_READYZ_URL", "http://127.0.0.1:8765/readyz")
    try:
        with urllib.request.urlopen(endpoint, timeout=timeout) as response:
            payload = json.load(response)
    except Exception as exc:
        raise ValueError(f"unable to query live Local Workspace bridge readiness at {endpoint}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("service") != "hermes-mcp-bridge":
        raise ValueError("live Local Workspace readiness response is not a hermes-mcp-bridge status object")
    if payload.get("ready") is not True or payload.get("ok") is not True:
        raise ValueError("live Local Workspace bridge is not ready")
    return payload


def validate_live_bridge_status(
    live: Mapping[str, Any],
    *,
    requirements: Mapping[str, Any],
    bound_compat: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    version = str(live.get("version") or "")
    minimum = str(requirements.get("minimum_version") or "")
    profile = str(live.get("tool_profile") or "")
    required_profile = str(bound_compat.get("required_profile") or "")
    capabilities = live.get("capability_contract") if isinstance(live.get("capability_contract"), Mapping) else {}
    active_caps = {str(x) for x in capabilities.get("capabilities") or []}
    required_caps = {str(x) for x in requirements.get("required_capabilities") or []}

    if live.get("ready") is not True or live.get("ok") is not True:
        errors.append("live Local Workspace bridge is not ready")
    if minimum and _version_tuple(version) < _version_tuple(minimum):
        errors.append(f"live Local Workspace bridge version {version or 'unknown'} is below required {minimum}")
    if required_profile and profile != required_profile:
        errors.append(f"live Local Workspace tool profile changed since binding: {profile or 'unknown'} != {required_profile}")
    missing_caps = sorted(required_caps - active_caps)
    if missing_caps:
        errors.append("live Local Workspace bridge is missing required capabilities: " + ", ".join(missing_caps))

    for key, live_key in (
        ("actual_version", "version"),
        ("tool_names_sha256", "tool_names_sha256"),
        ("source_commit", "source_commit"),
    ):
        expected = str(bound_compat.get(key) or "")
        actual = str(live.get(live_key) or "")
        if not expected:
            errors.append(f"workflow.bootstrap.bridge_compatibility.{key} is missing; rebind against the live bridge")
        elif actual != expected:
            errors.append(f"live Local Workspace {live_key} changed since binding")

    return errors

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _git(repo: Path, *args: str, timeout: float = 15.0) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 124, "", f"{type(exc).__name__}: {exc}"


def infer_lane(goal: str, lane: str = "auto") -> str:
    requested = str(lane or "auto").strip().lower()
    if requested not in LANES:
        raise ValueError(f"lane must be one of {sorted(LANES)}")
    if requested != "auto":
        return requested
    text = (goal or "").lower()
    business_terms = ("release", "product", "marketing", "promo", "launch", "repository", "software")
    animation_terms = ("episode", "season", "show", "character", "animated series", "cartoon")
    if any(term in text for term in business_terms):
        return "business"
    if any(term in text for term in animation_terms):
        return "animation"
    return "cinematic"


def _load_contract(repo: Path) -> dict[str, Any]:
    path = repo / "workflow" / "CURRENT.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("workflow/CURRENT.json schema_version must be 1")
    if not data.get("workflow_id") or not data.get("workflow_version"):
        raise ValueError("workflow/CURRENT.json requires workflow_id and workflow_version")
    compat = data.get("bridge_compatibility")
    if not isinstance(compat, Mapping):
        raise ValueError("workflow/CURRENT.json requires bridge_compatibility")
    if not isinstance(compat.get("minimum_version"), str) or not compat.get("minimum_version"):
        raise ValueError("bridge_compatibility.minimum_version is required")
    for key in ("required_tools", "required_capabilities"):
        value = compat.get(key)
        if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
            raise ValueError(f"bridge_compatibility.{key} must be a non-empty string list")
    return data


def _selected_docs(contract: Mapping[str, Any], lane: str) -> list[str]:
    docs: list[str] = []
    for value in list(contract.get("core_docs") or []) + list((contract.get("lane_docs") or {}).get(lane) or []):
        if isinstance(value, str) and value and value not in docs:
            docs.append(value)
    return docs


def bootstrap(
    *,
    repo: Path | None = None,
    goal: str = "",
    lane: str = "auto",
    refresh_remote: bool = True,
    allow_unverified_remote: bool = False,
) -> dict[str, Any]:
    repo = (repo or ROOT).expanduser().resolve()
    selected_lane = infer_lane(goal, lane)
    contract_path = repo / "workflow" / "CURRENT.json"
    blockers: list[str] = []
    warnings: list[str] = []

    if not contract_path.is_file():
        return {
            "ready": False,
            "blockers": ["workflow_manifest_missing"],
            "action": f"restore {contract_path}",
            "repo": str(repo),
        }

    try:
        contract = _load_contract(repo)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "ready": False,
            "blockers": ["workflow_manifest_invalid"],
            "error": str(exc),
            "repo": str(repo),
        }

    manifest_sha = _sha256_file(contract_path)
    docs = _selected_docs(contract, selected_lane)
    doc_records: list[dict[str, Any]] = []
    for relative in docs:
        path = repo / relative
        exists = path.is_file()
        digest = _sha256_file(path) if exists else None
        doc_records.append({"path": relative, "exists": exists, "sha256": digest})
        if not exists:
            blockers.append(f"required_doc_missing:{relative}")

    digest_payload = "\n".join(
        f"{item['path']}:{item['sha256'] or 'MISSING'}" for item in doc_records
    ).encode("utf-8")
    docs_sha = _sha256_bytes(digest_payload)

    fetch = {"attempted": bool(refresh_remote), "ok": None, "error": None}
    if refresh_remote:
        code, _, err = _git(repo, "fetch", "--quiet", "--prune", "origin", timeout=20.0)
        fetch["ok"] = code == 0
        fetch["error"] = None if code == 0 else (err or f"git fetch exited {code}")
        if code != 0 and not allow_unverified_remote:
            blockers.append("remote_freshness_unverified")
        elif code != 0:
            warnings.append("remote_freshness_unverified_override")

    _, head, _ = _git(repo, "rev-parse", "HEAD")
    _, branch, _ = _git(repo, "branch", "--show-current")
    up_code, upstream, _ = _git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    ahead = behind = None
    if up_code == 0 and upstream:
        c, counts, _ = _git(repo, "rev-list", "--left-right", "--count", f"HEAD...{upstream}")
        if c == 0 and counts:
            parts = counts.replace("\t", " ").split()
            if len(parts) >= 2:
                ahead, behind = int(parts[0]), int(parts[1])
                if behind > 0:
                    blockers.append(f"repo_behind_upstream:{behind}")
    else:
        warnings.append("git_upstream_unavailable")

    _, porcelain, _ = _git(repo, "status", "--porcelain")
    dirty_paths = []
    for line in porcelain.splitlines():
        if not line.strip():
            continue
        raw = line[3:] if len(line) >= 4 else line
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        dirty_paths.append(raw.strip())
    workflow_paths = {"workflow/CURRENT.json", *docs}
    workflow_dirty = sorted(path for path in dirty_paths if path in workflow_paths)
    if workflow_dirty:
        blockers.extend(f"workflow_file_dirty:{path}" for path in workflow_dirty)
    elif dirty_paths:
        warnings.append("repository_has_unrelated_worktree_changes")

    remote_verified = bool(refresh_remote and fetch.get("ok") is True and behind is not None)
    if behind and behind > 0:
        freshness = "STALE"
    elif remote_verified:
        freshness = "CURRENT"
    elif allow_unverified_remote:
        freshness = "UNVERIFIED_OVERRIDE"
    else:
        freshness = "LOCAL_TRACKING_ONLY"

    receipt = {
        "workflow_id": contract["workflow_id"],
        "workflow_version": contract["workflow_version"],
        "manifest_sha256": manifest_sha,
        "docs_sha256": docs_sha,
        "lane": selected_lane,
    }
    receipt_sha = _sha256_bytes(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )

    return {
        "ready": not blockers,
        "workflow_id": contract["workflow_id"],
        "workflow_version": contract["workflow_version"],
        "lane": selected_lane,
        "repo": str(repo),
        "repo_head": head or None,
        "branch": branch or None,
        "upstream": upstream or None,
        "ahead": ahead,
        "behind": behind,
        "freshness": freshness,
        "remote_refresh": fetch,
        "manifest_path": str(contract_path),
        "manifest_sha256": manifest_sha,
        "required_tool_profile": contract.get("required_tool_profile"),
        "bridge_compatibility_requirements": dict(contract.get("bridge_compatibility") or {}),
        "bridge_compatibility": {
            "evaluated": False,
            "compatible": False,
            "reason": "repository-native bootstrap cannot inspect the active Local Workspace bridge",
        },
        "required_docs": doc_records,
        "docs_sha256": docs_sha,
        "workflow_dirty_paths": workflow_dirty,
        "warnings": warnings,
        "blockers": blockers,
        "receipt": receipt,
        "receipt_sha256": receipt_sha,
        "directive": (
            "Read the returned required_docs before planning serious video work. "
            "Bind receipt_sha256 plus the receipt fields into the production manifest. "
            "Do not render when ready=false unless discovery_mode was explicitly chosen."
        ),
    }


def binding_status(
    data: Mapping[str, Any],
    *,
    repo: Path | None = None,
    refresh_remote: bool = False,
    active_bootstrap: Mapping[str, Any] | None = None,
    live_bridge_status: Mapping[str, Any] | None = None,
    require_active_bridge: bool = False,
) -> dict[str, Any]:
    workflow = data.get("workflow") if isinstance(data.get("workflow"), Mapping) else {}
    required = bool(workflow.get("bootstrap_required"))
    bound = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), Mapping) else {}
    if not required:
        return {"required": False, "ok": True, "legacy_or_explicitly_unbound": True}

    lane = str(bound.get("lane") or data.get("lane") or "auto")
    if lane == "animation" and data.get("lane") == "business":
        lane = "business"
    current = bootstrap(
        repo=repo,
        lane=lane,
        refresh_remote=refresh_remote,
        allow_unverified_remote=bool(bound.get("allow_unverified_remote")),
    )
    expected = current.get("receipt") or {}
    errors: list[str] = []
    for key in ("workflow_id", "workflow_version", "manifest_sha256", "docs_sha256", "lane"):
        if bound.get(key) != expected.get(key):
            errors.append(f"workflow.bootstrap.{key} is stale or missing")
    if bound.get("receipt_sha256") != current.get("receipt_sha256"):
        errors.append("workflow.bootstrap.receipt_sha256 is stale or missing")
    if not current.get("ready"):
        errors.extend(str(x) for x in current.get("blockers") or [])

    requirements = current.get("bridge_compatibility_requirements") or {}
    bound_compat = bound.get("bridge_compatibility") if isinstance(bound.get("bridge_compatibility"), Mapping) else {}
    if bound_compat.get("evaluated") is not True or bound_compat.get("compatible") is not True:
        errors.append("workflow.bootstrap.bridge_compatibility is missing or was not evaluated by Local Workspace")
    if bound_compat.get("minimum_version") != requirements.get("minimum_version"):
        errors.append("workflow.bootstrap.bridge_compatibility.minimum_version is stale")
    if bound_compat.get("required_profile") != current.get("required_tool_profile"):
        errors.append("workflow.bootstrap.bridge_compatibility.required_profile is stale")
    if bound_compat.get("missing_tools") not in ([], None):
        errors.append("workflow.bootstrap.bridge_compatibility recorded missing tools")
    if bound_compat.get("missing_capabilities") not in ([], None):
        errors.append("workflow.bootstrap.bridge_compatibility recorded missing capabilities")

    if require_active_bridge:
        if not isinstance(live_bridge_status, Mapping):
            errors.append("live Local Workspace bridge status is required before render dispatch")
        else:
            errors.extend(
                validate_live_bridge_status(
                    live_bridge_status,
                    requirements=requirements,
                    bound_compat=bound_compat,
                )
            )
    return {
        "required": True,
        "ok": not errors,
        "errors": errors,
        "bound": dict(bound),
        "current": {
            "workflow_id": current.get("workflow_id"),
            "workflow_version": current.get("workflow_version"),
            "manifest_sha256": current.get("manifest_sha256"),
            "docs_sha256": current.get("docs_sha256"),
            "lane": current.get("lane"),
            "receipt_sha256": current.get("receipt_sha256"),
            "freshness": current.get("freshness"),
            "repo_head": current.get("repo_head"),
            "bridge_compatibility_requirements": current.get("bridge_compatibility_requirements"),
        },
    }


def bind_manifest(
    data: dict[str, Any],
    bootstrap_result: Mapping[str, Any],
    *,
    allow_unverified_remote: bool = False,
) -> dict[str, Any]:
    if not bootstrap_result.get("ready") and not allow_unverified_remote:
        raise ValueError("workflow bootstrap is not ready: " + ", ".join(bootstrap_result.get("blockers") or []))
    receipt = dict(bootstrap_result.get("receipt") or {})
    if not receipt or not bootstrap_result.get("receipt_sha256"):
        raise ValueError("workflow bootstrap result has no receipt")
    compatibility = bootstrap_result.get("bridge_compatibility")
    if not isinstance(compatibility, Mapping) or compatibility.get("evaluated") is not True or compatibility.get("compatible") is not True:
        raise ValueError(
            "workflow binding requires a Local Workspace bootstrap result with evaluated compatible bridge evidence"
        )
    workflow = data.setdefault("workflow", {})
    workflow["bootstrap_required"] = True
    workflow["bootstrap"] = {
        **receipt,
        "receipt_sha256": bootstrap_result["receipt_sha256"],
        "repo_head": bootstrap_result.get("repo_head"),
        "freshness_at_bind": bootstrap_result.get("freshness"),
        "allow_unverified_remote": bool(allow_unverified_remote),
        "bridge_compatibility": {
            "evaluated": True,
            "compatible": True,
            "minimum_version": compatibility.get("minimum_version"),
            "actual_version": compatibility.get("actual_version"),
            "required_profile": compatibility.get("required_profile"),
            "active_profile": compatibility.get("active_profile"),
            "missing_tools": list(compatibility.get("missing_tools") or []),
            "missing_capabilities": list(compatibility.get("missing_capabilities") or []),
            "tool_names_sha256": compatibility.get("tool_names_sha256"),
            "source_commit": compatibility.get("source_commit"),
        },
    }
    return data
