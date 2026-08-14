"""Per-stage commands, run --from --to (skipping cached), status (what's
stale and why).

manifest, qc, and report are wired to their real B2/B3/B5 stage runners.
extract/train/evaluate/infer (B7) and kinematics are registered but not
implemented: kinematics' pure computational core (B4) is fully built and
tested, but its CLI-level file-reading wrapper needs stage 7's pose output
format, which doesn't exist until B7 -- itself scaffold-only. See
QUESTIONS.md b6-kinematics-not-wired.

Idempotency (invariant 4): a stage is skipped when its provenance sidecar's
input+config hashes already match a freshly computed set -- Stage.status()
is the single place that decision is made, so `run` and `status` never
disagree with each other.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from pipeline.config import AnalysisConfig
from pipeline.provenance import Provenance, hash_config, hash_file, provenance_path_for
from pipeline.stages.manifest import compute_manifest_input_hashes, write_manifest
from pipeline.stages.qc_gate import write_qc_gate
from pipeline.stages.report import write_report


class StageNotImplementedError(NotImplementedError):
    pass


def derived_path(config: AnalysisConfig, name: str) -> Path:
    return Path(config.paths.derived_root) / name


def config_hash_for(config: AnalysisConfig) -> str:
    """One hash for the whole config, deliberately coarse: any config
    change invalidates every stage rather than trying to scope which
    section belongs to which stage. Over-invalidation costs a rerun;
    under-invalidation would risk silently stale output, which is worse."""
    return hash_config(dataclasses.asdict(config))


@dataclass(frozen=True)
class StageStatus:
    name: str
    state: str  # "not_implemented" | "missing" | "blocked" | "stale" | "up_to_date"
    detail: str


@dataclass(frozen=True)
class Stage:
    name: str
    output_artifact: Callable[[AnalysisConfig], Path]
    compute_input_hashes: Callable[[AnalysisConfig], dict[str, str]] | None
    run_fn: Callable[[AnalysisConfig, str], Provenance] | None  # None => not implemented

    def status(self, config: AnalysisConfig) -> StageStatus:
        if self.run_fn is None:
            return StageStatus(self.name, "not_implemented", "stage not wired into the CLI yet")

        artifact = self.output_artifact(config)
        prov_path = provenance_path_for(artifact)
        if not artifact.exists() or not prov_path.exists():
            return StageStatus(self.name, "missing", f"{artifact} does not exist yet")

        try:
            fresh_hashes = self.compute_input_hashes(config) if self.compute_input_hashes else {}
        except FileNotFoundError as exc:
            return StageStatus(self.name, "blocked", f"input artifact missing: {exc}")

        existing = Provenance.read_json(prov_path)
        if existing.matches_inputs(fresh_hashes, config_hash_for(config)):
            return StageStatus(self.name, "up_to_date", "inputs and config unchanged since last run")
        return StageStatus(self.name, "stale", "inputs or config changed since last run")

    def run(self, config: AnalysisConfig, dry_run: bool) -> Provenance | None:
        if self.run_fn is None:
            raise StageNotImplementedError(f"stage {self.name!r} is not implemented")
        status = self.status(config)
        if status.state == "up_to_date" or dry_run:
            return None
        return self.run_fn(config, config_hash_for(config))


# -- stage wiring --

def _manifest_input_hashes(config: AnalysisConfig) -> dict[str, str]:
    return compute_manifest_input_hashes(config.paths.archive_root)


def _run_manifest(config: AnalysisConfig, config_hash: str) -> Provenance:
    return write_manifest(config.paths.archive_root, config.views, derived_path(config, "manifest.parquet"), config_hash)


def _qc_input_hashes(config: AnalysisConfig) -> dict[str, str]:
    return {"manifest.parquet": hash_file(derived_path(config, "manifest.parquet"))}


def _run_qc(config: AnalysisConfig, config_hash: str) -> Provenance:
    return write_qc_gate(
        derived_path(config, "manifest.parquet"), derived_path(config, "manifest_qc.parquet"),
        config.qc, config_hash,
    )


def _report_output(config: AnalysisConfig) -> Path:
    return derived_path(config, "report") / "summary_overall.parquet"


def _report_input_hashes(config: AnalysisConfig) -> dict[str, str]:
    return {
        "trial_summary.parquet": hash_file(derived_path(config, "trial_summary.parquet")),
        "kinematics_long.parquet": hash_file(derived_path(config, "kinematics_long.parquet")),
    }


def _run_report(config: AnalysisConfig, config_hash: str) -> Provenance:
    return write_report(
        derived_path(config, "trial_summary.parquet"), derived_path(config, "kinematics_long.parquet"),
        derived_path(config, "report"), config_hash,
    )


STAGE_REGISTRY: list[Stage] = [
    Stage("manifest", lambda c: derived_path(c, "manifest.parquet"), _manifest_input_hashes, _run_manifest),
    Stage("qc", lambda c: derived_path(c, "manifest_qc.parquet"), _qc_input_hashes, _run_qc),
    Stage("extract", lambda c: derived_path(c, "frames_manifest.csv"), None, None),
    Stage("train", lambda c: derived_path(c, "training_log.json"), None, None),
    Stage("evaluate", lambda c: derived_path(c, "evaluation_report.json"), None, None),
    Stage("infer", lambda c: derived_path(c, "pose_index.parquet"), None, None),
    Stage("kinematics", lambda c: derived_path(c, "kinematics_long.parquet"), None, None),
    Stage("report", _report_output, _report_input_hashes, _run_report),
]

STAGE_NAMES = [s.name for s in STAGE_REGISTRY]
STAGES_BY_NAME = {s.name: s for s in STAGE_REGISTRY}


def status_report(config: AnalysisConfig, registry: list[Stage] = STAGE_REGISTRY) -> list[StageStatus]:
    return [stage.status(config) for stage in registry]


def run_pipeline(
    config: AnalysisConfig,
    from_stage: str,
    to_stage: str,
    dry_run: bool = False,
    registry: list[Stage] = STAGE_REGISTRY,
) -> list[tuple[str, str]]:
    """Runs stages from_stage..to_stage inclusive, in registry order,
    skipping any stage already up_to_date (resumability, invariant 4)."""
    names = [s.name for s in registry]
    if from_stage not in names or to_stage not in names:
        raise ValueError(f"unknown stage in range [{from_stage!r}, {to_stage!r}]")
    start, end = names.index(from_stage), names.index(to_stage)
    if start > end:
        raise ValueError(f"--from {from_stage!r} comes after --to {to_stage!r} in pipeline order")

    results: list[tuple[str, str]] = []
    for stage in registry[start : end + 1]:
        status = stage.status(config)
        if status.state == "up_to_date":
            results.append((stage.name, "skipped_up_to_date"))
            continue
        if dry_run:
            results.append((stage.name, f"would_run ({status.state})"))
            continue
        stage.run(config, dry_run=False)
        results.append((stage.name, "ran"))
    return results
