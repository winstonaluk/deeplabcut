from __future__ import annotations

from datetime import datetime, timezone

from pipeline.provenance import (
    Provenance,
    current_code_commit,
    hash_config,
    hash_file,
    make_provenance,
    provenance_path_for,
)


def test_hash_file_is_deterministic_and_content_sensitive(tmp_path):
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    a.write_bytes(b"hello world")
    b.write_bytes(b"hello world")
    c = tmp_path / "c.bin"
    c.write_bytes(b"different content")

    assert hash_file(a) == hash_file(b)
    assert hash_file(a) != hash_file(c)


def test_hash_config_is_stable_under_key_reordering():
    h1 = hash_config({"a": 1, "b": 2})
    h2 = hash_config({"b": 2, "a": 1})
    h3 = hash_config({"a": 1, "b": 3})

    assert h1 == h2
    assert h1 != h3


def test_current_code_commit_returns_something_in_this_repo():
    commit = current_code_commit(repo_root=None)
    assert commit != ""  # either a real short hash or "unknown", never empty


def test_provenance_round_trip(tmp_path):
    prov = make_provenance(
        stage_name="build_manifest",
        stage_version="1.0.0",
        input_hashes={"session_dir": "abc123"},
        config_hash="def456",
        now=datetime(2026, 8, 11, tzinfo=timezone.utc),
    )
    path = provenance_path_for(tmp_path / "manifest.parquet")
    prov.write_json(path)

    assert path.name == "manifest.parquet.provenance.json"
    reloaded = Provenance.read_json(path)
    assert reloaded == prov


def test_matches_inputs_detects_identical_and_changed_state():
    prov = make_provenance(
        stage_name="qc_gate", stage_version="1.0.0",
        input_hashes={"manifest": "aaa"}, config_hash="bbb",
    )

    assert prov.matches_inputs({"manifest": "aaa"}, "bbb") is True
    assert prov.matches_inputs({"manifest": "changed"}, "bbb") is False
    assert prov.matches_inputs({"manifest": "aaa"}, "changed_config") is False
