from pathlib import Path

import pytest

from app.config import ConfigError, load_config

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


def test_load_config_has_every_key_and_default():
    config = load_config(CONFIG_PATH)

    assert config.cameras  # N-camera by construction: at least one entry
    assert config.capture.fps == 30
    assert config.capture.queue_maxsize == 120
    assert config.trial_timing.min_trial_duration_s == 5
    assert config.trial_timing.suspicious_duration_s == 30
    assert config.trial_timing.max_trial_duration_s == 600
    assert config.keymap == {
        "F": "fall",
        "Z": "freeze",
        "D": "did_not_descend",
        "E": "experimenter_error",
        "V": "other_invalid",
    }
    assert set(config.reason_code_labels) == set(config.keymap.values())
    assert config.storage.filename_include_view_token is False
    assert config.encoder.codec == "h264_qsv"
    assert config.encoder.fallback_codec == "libx264"


def test_load_config_rejects_missing_top_level_key(tmp_path):
    bad = tmp_path / "config.toml"
    bad.write_text("[app]\nversion = '0.1'\nrig_id = 'r'\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(bad)


def test_load_config_rejects_empty_camera_list(tmp_path):
    text = CONFIG_PATH.read_text(encoding="utf-8")
    # Strip the [[cameras]] table entirely.
    lines = text.splitlines()
    out, skipping = [], False
    for line in lines:
        if line.strip() == "[[cameras]]":
            skipping = True
            continue
        if skipping and line.strip().startswith("["):
            skipping = False
        if not skipping:
            out.append(line)
    bad = tmp_path / "config.toml"
    bad.write_text("\n".join(out), encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(bad)
