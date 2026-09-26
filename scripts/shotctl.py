#!/usr/bin/env python3
"""Preview / inspect / revise individual shots before productionctl delivery."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.core.shot_workflow import render, record_review, status

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['status', 'preview', 'motion', 'review'])
    parser.add_argument('spec')
    parser.add_argument('--shot')
    parser.add_argument('--stage', choices=['preview', 'motion'])
    parser.add_argument('--review-file')
    parser.add_argument('--timeout', type=float, default=300)
    args = parser.parse_args()
    try:
        if args.command == 'status':
            result = status(args.spec)
        elif not args.shot:
            parser.error('--shot is required')
        elif args.command == 'review':
            if not args.stage or not args.review_file:
                parser.error('--stage and --review-file are required')
            result = record_review(args.spec, args.shot, args.stage, args.review_file)
        else:
            result = render(args.spec, args.shot, args.command, args.timeout)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        print(f'FAIL {exc}', file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
