#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.workflow_contract import bootstrap, bind_manifest, query_live_bridge_status, validate_live_bridge_status


def main() -> int:
    p = argparse.ArgumentParser(description="Resolve and bind the current Chatgpt-Video-Creations workflow.")
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("bootstrap")
    b.add_argument("--goal", default="")
    b.add_argument("--lane", default="auto", choices=["auto", "cinematic", "animation", "business"])
    b.add_argument("--no-refresh-remote", action="store_true")
    b.add_argument("--allow-unverified-remote", action="store_true")

    bind = sub.add_parser("bind")
    bind.add_argument("manifest")
    bind.add_argument("--goal", default="")
    bind.add_argument("--lane", default="auto", choices=["auto", "cinematic", "animation", "business"])
    bind.add_argument("--allow-unverified-remote", action="store_true")
    bind.add_argument(
        "--bootstrap-result",
        help="JSON file containing the current Local Workspace video_workflow_bootstrap result; required for production binding.",
    )

    args = p.parse_args()
    result = bootstrap(
        goal=getattr(args, "goal", ""),
        lane=getattr(args, "lane", "auto"),
        refresh_remote=not getattr(args, "no_refresh_remote", False),
        allow_unverified_remote=getattr(args, "allow_unverified_remote", False),
    )
    if args.command == "bootstrap":
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ready") else 2

    if args.bootstrap_result:
        bootstrap_path = Path(args.bootstrap_result).expanduser().resolve()
        result = json.loads(bootstrap_path.read_text(encoding="utf-8"))

    compatibility = result.get("bridge_compatibility")
    requirements = result.get("bridge_compatibility_requirements")
    if not isinstance(compatibility, dict) or compatibility.get("evaluated") is not True:
        raise ValueError("production binding requires an evaluated Local Workspace bootstrap result")
    if not isinstance(requirements, dict):
        raise ValueError("bootstrap result is missing bridge compatibility requirements")

    live = query_live_bridge_status()
    live_errors = validate_live_bridge_status(
        live,
        requirements=requirements,
        bound_compat={
            **compatibility,
            "tool_names_sha256": live.get("tool_names_sha256"),
            "source_commit": live.get("source_commit"),
        },
    )
    if live_errors:
        raise ValueError("live Local Workspace bridge does not match bootstrap evidence: " + "; ".join(live_errors))
    compatibility["tool_names_sha256"] = live.get("tool_names_sha256")
    compatibility["source_commit"] = live.get("source_commit")
    compatibility["boot_id_at_bind"] = live.get("boot_id")

    path = Path(args.manifest).expanduser().resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    bind_manifest(data, result, allow_unverified_remote=args.allow_unverified_remote)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)
    print(json.dumps({"bound": True, "manifest": str(path), "bootstrap": data["workflow"]["bootstrap"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
