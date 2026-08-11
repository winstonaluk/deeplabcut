from pathlib import Path

import pytest

from pipeline.config import ConfigError, load_config

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


def test_load_config_has_every_key_and_default():
    config = load_config(CONFIG_PATH)

    assert config.views == ("lateral_L",)
    assert config.keypoints.primary_keypoint == "mid_back"
    assert "pole_top" in config.keypoints.pole_landmarks
    assert config.qc.max_dropped_frame_rate == 0.02
    assert config.qc.min_duration_s == 5.0
    assert config.kinematics.max_gap_frames == 5
    assert config.kinematics.descent_rule_name == "threshold_crossing_v1"
    assert config.pole_length_mm == 1000.0
    assert config.analysis_fps == 30
    assert len(config.calibration_epochs) == 1
    assert config.calibration_epochs[0].epoch_id == "epoch-2026-01"


def test_load_config_rejects_missing_top_level_key(tmp_path):
    bad = tmp_path / "config.toml"
    bad.write_text("[paths]\narchive_root = 'x'\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(bad)


def test_load_config_rejects_primary_keypoint_outside_scheme(tmp_path):
    text = CONFIG_PATH.read_text(encoding="utf-8").replace(
        'primary_keypoint = "mid_back"', 'primary_keypoint = "nonexistent_point"'
    )
    bad = tmp_path / "config.toml"
    bad.write_text(text, encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(bad)


def test_load_config_rejects_empty_views_list(tmp_path):
    text = CONFIG_PATH.read_text(encoding="utf-8").replace(
        'list = ["lateral_L"]', "list = []"
    )
    bad = tmp_path / "config.toml"
    bad.write_text(text, encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(bad)
