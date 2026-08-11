"""CLI entry point.

    python -m app --mock   # synthetic frames, no hardware
    python -m app          # real camera via Spinnaker/PySpin
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from app.config import load_config

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="app", description="PDCT acquisition GUI")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use MockCamera instead of SpinnakerCamera. No hardware required.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to config.toml (default: acquisition/config.toml)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    logging.basicConfig(level=getattr(logging, config.log_level.upper(), logging.INFO))

    # Wired once the GUI screens exist (A5 session setup, A6 recording).
    # Until then this is a config-loading/preflight smoke entry point only.
    raise NotImplementedError(
        "GUI not wired yet -- session setup (A5) and recording (A6) screens "
        "are not implemented. Config loaded and validated successfully: "
        f"paradigm={config.active_paradigm!r}, mock={args.mock!r}"
    )


if __name__ == "__main__":
    sys.exit(main())
