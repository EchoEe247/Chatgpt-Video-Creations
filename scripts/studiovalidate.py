#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.studio_validation import (
    freeze_benchmark,
    freeze_findings,
    make_operational_handoff,
    score_benchmark,
    score_operational_handoff,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Controlled studio validation benchmark.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("freeze")
    p.add_argument("--output", required=True)

    p = sub.add_parser("freeze-findings")
    p.add_argument("--package", required=True)
    p.add_argument("--findings", required=True)
    p.add_argument("--contamination", required=True, choices=["BLINDED", "PARTIALLY_BLINDED", "NOT_BLINDED"])
    p.add_argument("--context-exposure", action="append", default=[])

    p = sub.add_parser("score")
    p.add_argument("--package", required=True)

    p = sub.add_parser("handoff")
    p.add_argument("--output", required=True)
    p.add_argument("--bridge-commit", required=True)
    p.add_argument("--video-commit", required=True)

    p = sub.add_parser("score-handoff")
    p.add_argument("--package", required=True)
    p.add_argument("--report", required=True)

    args = parser.parse_args()
    if args.command == "freeze":
        result = freeze_benchmark(Path(args.output))
    elif args.command == "freeze-findings":
        result = freeze_findings(
            Path(args.package),
            Path(args.findings),
            contamination_status=args.contamination,
            context_exposure=args.context_exposure,
        )
    elif args.command == "score":
        result = score_benchmark(Path(args.package))
    elif args.command == "handoff":
        result = make_operational_handoff(
            Path(args.output),
            bridge_commit=args.bridge_commit,
            video_commit=args.video_commit,
        )
    else:
        result = score_operational_handoff(Path(args.package), Path(args.report))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
