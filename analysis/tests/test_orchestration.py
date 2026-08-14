"""Checkpoint B6: per-stage commands, run --from --to, status, --dry-run.
Idempotency and resumability tested with fake artifacts, plus a real
integration pass through manifest -> qc -> report via the real registry."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pipeline.config import (
    AnalysisConfig,
    CalibrationEpoch,
    KeypointsConfig,
    KinematicsConfig,
    PathsConfig,
    QCConfig,
)
from pipeline.contracts import KinematicsLongRow, TrialSummaryRow
from pipeline.orchestration import (
    STAGES_BY_NAME,
    Stage,
    StageNotImplementedError,
    run_pipeline,
    status_report,
)
from pipeline.provenance import hash_file, make_provenance, provenance_path_for
from pipeline.stages.manifest import trial_uid
from schema.session_metadata import CameraInfo, SessionMetadata
from schema.trials import TrialRecord, write_trials_csv


def _config(tmp_path: Path, pole_length_mm: float = 1000.0) -> AnalysisConfig:
    return AnalysisConfig(
        paths=PathsConfig(
            archive_root=str(tmp_path / "archive"), local_cache_root=str(tmp_path / "cache"),
            derived_root=str(tmp_path / "derived"), dlc_project_path=str(tmp_path / "dlc"),
        ),
        views=("lateral_L",),
        keypoints=KeypointsConfig(scheme=("mid_back",), pole_landmarks=(), primary_keypoint="mid_back"),
        superanimal_init={"lateral_L": "SuperAnimal-Quadruped"},
        qc=QCConfig(nominal_fps=30.0, max_dropped_frame_rate=0.02, min_duration_s=1.0, max_duration_s=600.0, max_fps_deviation=2.0),
        pole_length_mm=pole_length_mm,
        kinematics=KinematicsConfig(
            likelihood_cutoff=0.5, max_gap_frames=5, smoothing_method="median", smoothing_window=3,
            descent_rule_name="threshold_crossing_v1", descent_rule_onset_height_fraction=0.95,
            descent_rule_offset_height_fraction=0.05, pole_landmark_drift_threshold_mm=5.0,
        ),
        evaluation_max_pixel_error=10.0, analysis_fps=30, inference_batch_size=8,
        calibration_epochs=(CalibrationEpoch("s", "e1", "20260101", "99991231", "cal.json"),),
    )


# -- fake stages: idempotency and resumability --

def _fake_chain(tmp_path):
    """Two fake stages, the second depending on the first's output content
    (like qc depends on manifest) -- so re-running stage 1 with different
    content should cascade a "stale" status onto stage 2."""
    calls: list[str] = []

    def out1(c: AnalysisConfig) -> Path:
        return Path(c.paths.derived_root) / "fake1.txt"

    def hashes1(c: AnalysisConfig) -> dict[str, str]:
        return {"seed": "fixed"}

    def run1(c: AnalysisConfig, config_hash: str):
        calls.append("stage1")
        path = out1(c)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"content-{len(calls)}", encoding="utf-8")
        prov = make_provenance("stage1", "1.0", hashes1(c), config_hash)
        prov.write_json(provenance_path_for(path))
        return prov

    def out2(c: AnalysisConfig) -> Path:
        return Path(c.paths.derived_root) / "fake2.txt"

    def hashes2(c: AnalysisConfig) -> dict[str, str]:
        return {"stage1_output": hash_file(out1(c))}

    def run2(c: AnalysisConfig, config_hash: str):
        calls.append("stage2")
        path = out2(c)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("stage2-content", encoding="utf-8")
        prov = make_provenance("stage2", "1.0", hashes2(c), config_hash)
        prov.write_json(provenance_path_for(path))
        return prov

    registry = [Stage("stage1", out1, hashes1, run1), Stage("stage2", out2, hashes2, run2)]
    return registry, calls


def test_stage_status_missing_before_first_run(tmp_path):
    registry, calls = _fake_chain(tmp_path)
    config = _config(tmp_path)
    assert registry[0].status(config).state == "missing"


def test_stage_run_then_status_up_to_date(tmp_path):
    registry, calls = _fake_chain(tmp_path)
    config = _config(tmp_path)

    registry[0].run(config, dry_run=False)
    assert calls == ["stage1"]
    assert registry[0].status(config).state == "up_to_date"


def test_stage_run_is_a_noop_when_already_up_to_date(tmp_path):
    registry, calls = _fake_chain(tmp_path)
    config = _config(tmp_path)

    registry[0].run(config, dry_run=False)
    registry[0].run(config, dry_run=False)  # should skip, not append to calls
    assert calls == ["stage1"]


def test_dry_run_never_calls_run_fn_or_writes_artifact(tmp_path):
    registry, calls = _fake_chain(tmp_path)
    config = _config(tmp_path)

    registry[0].run(config, dry_run=True)
    assert calls == []
    assert not registry[0].output_artifact(config).exists()


def test_downstream_stage_goes_stale_when_upstream_output_changes(tmp_path):
    registry, calls = _fake_chain(tmp_path)
    config = _config(tmp_path)

    registry[0].run(config, dry_run=False)
    registry[1].run(config, dry_run=False)
    assert calls == ["stage1", "stage2"]
    assert registry[1].status(config).state == "up_to_date"

    # rerun stage1 by deleting its provenance to force a rerun, changing its content
    provenance_path_for(registry[0].output_artifact(config)).unlink()
    registry[0].run(config, dry_run=False)
    assert calls == ["stage1", "stage2", "stage1"]

    assert registry[1].status(config).state == "stale"


def test_stage_goes_stale_when_config_changes(tmp_path):
    registry, calls = _fake_chain(tmp_path)
    config_a = _config(tmp_path, pole_length_mm=1000.0)
    config_b = _config(tmp_path, pole_length_mm=2000.0)

    registry[0].run(config_a, dry_run=False)
    assert registry[0].status(config_a).state == "up_to_date"
    assert registry[0].status(config_b).state == "stale"


def test_run_pipeline_chains_and_skips_up_to_date(tmp_path):
    registry, calls = _fake_chain(tmp_path)
    config = _config(tmp_path)

    results = run_pipeline(config, "stage1", "stage2", dry_run=False, registry=registry)
    assert results == [("stage1", "ran"), ("stage2", "ran")]

    results2 = run_pipeline(config, "stage1", "stage2", dry_run=False, registry=registry)
    assert results2 == [("stage1", "skipped_up_to_date"), ("stage2", "skipped_up_to_date")]
    assert calls == ["stage1", "stage2"]  # no extra calls on the second pass


def test_run_pipeline_dry_run_reports_without_running(tmp_path):
    registry, calls = _fake_chain(tmp_path)
    config = _config(tmp_path)

    results = run_pipeline(config, "stage1", "stage2", dry_run=True, registry=registry)
    assert calls == []
    assert all("would_run" in outcome for _, outcome in results)


def test_run_pipeline_rejects_reversed_range(tmp_path):
    registry, calls = _fake_chain(tmp_path)
    config = _config(tmp_path)
    with pytest.raises(ValueError):
        run_pipeline(config, "stage2", "stage1", registry=registry)


def test_run_pipeline_rejects_unknown_stage_name(tmp_path):
    registry, calls = _fake_chain(tmp_path)
    config = _config(tmp_path)
    with pytest.raises(ValueError):
        run_pipeline(config, "nope", "stage1", registry=registry)


# -- real registry: not-implemented stages --

@pytest.mark.parametrize("name", ["extract", "train", "evaluate", "infer", "kinematics"])
def test_unwired_stage_reports_not_implemented(tmp_path, name):
    config = _config(tmp_path)
    status = STAGES_BY_NAME[name].status(config)
    assert status.state == "not_implemented"


@pytest.mark.parametrize("name", ["extract", "train", "evaluate", "infer", "kinematics"])
def test_unwired_stage_run_raises(tmp_path, name):
    config = _config(tmp_path)
    with pytest.raises(StageNotImplementedError):
        STAGES_BY_NAME[name].run(config, dry_run=False)


def test_status_report_lists_every_stage_in_order(tmp_path):
    config = _config(tmp_path)
    statuses = status_report(config)
    assert [s.name for s in statuses] == [
        "manifest", "qc", "extract", "train", "evaluate", "infer", "kinematics", "report",
    ]


# -- real integration: manifest -> qc via the real registry, then report standalone --

def _write_synthetic_session(archive_root, animal_id, trials):
    session_dir = archive_root / f"{animal_id}_pdct-pilot_20260811_WL"
    session_dir.mkdir(parents=True)
    meta = SessionMetadata(
        animal_id=animal_id, project_name="pdct-pilot", date="20260811", experimenter_initials="WL",
        session_start_timestamp="2026-08-11T09:00:00",
        cameras=(CameraInfo(serial="123", user_set_loaded="UserSet1", user_set_verified=True),),
        app_version="0.1.0", git_commit="deadbeef", ffmpeg_encoder="h264_qsv",
        ffmpeg_params="-global_quality 18", rig_id="rig-1",
    )
    meta.write_json(session_dir / "session_metadata.json")
    write_trials_csv(session_dir / "trials.csv", trials)
    for trial in trials:
        base = f"{animal_id}_pdct-pilot_20260811_WL_0905_t{trial.trial_number:03d}"
        (session_dir / f"{base}.mp4").write_bytes(b"fake")
        (session_dir / f"{base}_timestamps.csv").write_text("#schema_version=1\n", encoding="utf-8")
    return session_dir


def test_real_manifest_then_qc_via_orchestration(tmp_path):
    config = _config(tmp_path)
    Path(config.paths.archive_root).mkdir(parents=True)
    _write_synthetic_session(
        Path(config.paths.archive_root), "R042",
        [TrialRecord(trial_number=1, start_time="2026-08-11T09:05:00", duration_s=42.5,
                     flags=frozenset(), auto_flags=frozenset(), note="", n_frames=1275,
                     dropped_frames=0, achieved_fps=30.0)],
    )

    results = run_pipeline(config, "manifest", "qc", dry_run=False)
    assert results == [("manifest", "ran"), ("qc", "ran")]

    manifest_df = pd.read_parquet(Path(config.paths.derived_root) / "manifest.parquet")
    qc_df = pd.read_parquet(Path(config.paths.derived_root) / "manifest_qc.parquet")
    assert len(manifest_df) == 1
    assert len(qc_df) == 1
    assert qc_df.iloc[0]["included"] == True  # noqa: E712 -- explicit bool check reads clearer here

    # resumability: rerunning with nothing changed skips both
    results2 = run_pipeline(config, "manifest", "qc", dry_run=False)
    assert results2 == [("manifest", "skipped_up_to_date"), ("qc", "skipped_up_to_date")]


def test_real_report_stage_via_orchestration_with_fake_upstream_artifacts(tmp_path):
    """kinematics isn't wired (see QUESTIONS.md), so this places fake
    trial_summary/kinematics_long artifacts directly -- proving the report
    stage's orchestration wiring works standalone, independent of whether
    kinematics has run."""
    config = _config(tmp_path)
    derived = Path(config.paths.derived_root)
    derived.mkdir(parents=True)

    summary = TrialSummaryRow(
        trial_uid=trial_uid("R042", "pdct-pilot", "20260811", "WL", "lateral_L", 1),
        primary_keypoint="mid_back", descent_onset_frame=5, descent_offset_frame=50,
        descent_duration_s=1.5, mean_velocity_mm_s=400.0, occlusion_fraction=0.0,
        pole_landmark_drift_flagged=False,
    )
    long_row = KinematicsLongRow(
        trial_uid=summary.trial_uid, view="lateral_L", keypoint="mid_back", frame_index=0,
        x_mm=0.0, y_mm=500.0, height_fraction=0.5, velocity_mm_s=-400.0, likelihood=0.9,
        is_interpolated=False,
    )
    from dataclasses import asdict
    pd.DataFrame([asdict(summary)]).to_parquet(derived / "trial_summary.parquet", index=False)
    pd.DataFrame([asdict(long_row)]).to_parquet(derived / "kinematics_long.parquet", index=False)

    results = run_pipeline(config, "report", "report", dry_run=False)
    assert results == [("report", "ran")]
    assert (derived / "report" / "summary_overall.parquet").exists()
