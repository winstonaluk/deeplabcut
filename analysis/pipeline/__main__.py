"""CLI entry point.

    python -m pipeline manifest [--config path.toml] [--dry-run]
    python -m pipeline qc
    python -m pipeline extract | train | evaluate | infer | kinematics | report
    python -m pipeline run --from manifest --to qc [--dry-run]
    python -m pipeline status
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline.config import load_config
from pipeline.orchestration import STAGE_NAMES, STAGES_BY_NAME, run_pipeline, status_report

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipeline")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--dry-run", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in STAGE_NAMES:
        subparsers.add_parser(name)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--from", dest="from_stage", required=True, choices=STAGE_NAMES)
    run_parser.add_argument("--to", dest="to_stage", required=True, choices=STAGE_NAMES)

    subparsers.add_parser("status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)

    if args.command == "status":
        for s in status_report(config):
            print(f"{s.name:12s} {s.state:16s} {s.detail}")
        return 0

    if args.command == "run":
        for name, outcome in run_pipeline(config, args.from_stage, args.to_stage, dry_run=args.dry_run):
            print(f"{name:12s} {outcome}")
        return 0

    stage = STAGES_BY_NAME[args.command]
    if args.dry_run:
        status = stage.status(config)
        print(f"{stage.name}: {status.state} -- {status.detail}")
        return 0
    stage.run(config, dry_run=False)
    print(f"{stage.name}: done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
