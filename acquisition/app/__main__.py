"""CLI entry point.

    python -m app --mock --headless   # full session, synthetic frames
    python -m app --headless          # full session, real camera
    python -m app                     # HTTP API + browser UI (checkpoint A13)

``--headless`` drives a whole session with no UI at all -- preflight, N trials,
review artifacts -- which is how the recording path is proven before any UI
exists to blame. It is a smoke runner, not the lab workflow.
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
import sys
import time
from pathlib import Path

from app.config import AppConfig, load_config
from app.session_service import PreflightFailed, SessionService

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="app", description="PDCT acquisition")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use MockCamera for every camera. No hardware required.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run a scripted session and exit, with no UI.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to config.toml (default: acquisition/config.toml)",
    )
    parser.add_argument(
        "--session-root",
        type=Path,
        default=None,
        help="Override storage.session_root (relative paths resolve against cwd).",
    )
    parser.add_argument("--animal-id", default="mock01")
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument(
        "--trial-seconds",
        type=float,
        default=6.0,
        help="Must exceed trial_timing.min_trial_duration_s or the stop is swallowed.",
    )
    return parser.parse_args(argv)


def _with_session_root(config: AppConfig, session_root: Path | None) -> AppConfig:
    if session_root is None:
        return config
    storage = dataclasses.replace(config.storage, session_root=str(session_root))
    return dataclasses.replace(config, storage=storage)


def run_headless(config: AppConfig, args: argparse.Namespace) -> int:
    service = SessionService(config, mock=args.mock)

    result = service.preflight()
    for check in result.checks:
        print(f"  [{'PASS' if check.passed else 'FAIL'}] {check.describe()}")
    if not result.passed:
        print("\npreflight failed; not recording.")
        return 1

    try:
        session_dir = service.start_session(
            animal_id=args.animal_id,
            project_name=config.metadata.projects[0],
            experimenter_initials=config.metadata.experimenter_initials[0],
        )
    except PreflightFailed as exc:
        print(f"\n{exc}")
        return 1

    print(f"\nsession: {session_dir}")
    try:
        for _ in range(args.trials):
            service.toggle_trial()
            state = service.state()
            print(f"  trial {state.trial_number} recording...")
            time.sleep(args.trial_seconds)
            service.toggle_trial()
            record = service.trial_records()[-1]
            print(
                f"  trial {record.trial_number} stopped: {record.duration_s:.1f}s, "
                f"{record.n_frames} frames, {record.dropped_frames} dropped, "
                f"{record.achieved_fps:.2f} fps, auto_flags={sorted(record.auto_flags)}"
            )
    finally:
        service.end_session()

    print("\nartifacts:")
    for path in sorted(session_dir.iterdir()):
        print(f"  {path.name}  ({path.stat().st_size} bytes)")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = _with_session_root(load_config(args.config), args.session_root)
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.headless:
        return run_headless(config, args)

    print(
        "The HTTP API and browser UI are checkpoint A13 and are not built yet.\n"
        "Run a full session now with:\n\n"
        "    python -m app --mock --headless\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
