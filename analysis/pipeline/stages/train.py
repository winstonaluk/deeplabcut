"""Stage 5: train. SuperAnimal-initialized fine-tuning via the DLC Python API.

Requires DeepLabCut installed, a labeled dataset, and in practice a GPU --
not buildable unattended. This module defines the resumability check
(pure, testable without DLC); the training call itself is a thin wrapper.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.contracts import TrainingLog


def has_matching_training_run(training_log_path: Path, config_hash: str) -> bool:
    """Resumable: True iff a training_log.json already exists for this
    exact config hash -- retraining is expensive and shouldn't repeat for
    an unchanged config. Pure and testable without DLC."""
    if not training_log_path.exists():
        return False
    log = json.loads(training_log_path.read_text(encoding="utf-8"))
    return log.get("config_hash") == config_hash


def write_training_log(path: Path, log: TrainingLog) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "config_hash": log.config_hash, "seed": log.seed, "train_fraction": log.train_fraction,
                "snapshot_id": log.snapshot_id, "superanimal_init": log.superanimal_init,
            },
            indent=2, sort_keys=True,
        ),
        encoding="utf-8",
    )


def train(dlc_project_path: Path, superanimal_init: str, config_hash: str, seed: int = 42) -> TrainingLog:
    """Fine-tunes from the configured SuperAnimal init via
    deeplabcut.train_network(). Requires DeepLabCut installed, a labeled
    dataset, and in practice a GPU -- none available unattended."""
    raise NotImplementedError("requires DeepLabCut installed and a labeled dataset")
