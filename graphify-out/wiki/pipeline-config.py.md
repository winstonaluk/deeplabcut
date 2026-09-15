# pipeline/config.py

> 20 nodes

## Key Concepts

- **pipeline/config.py** (17 connections) — `analysis/pipeline/config.py`
- **load_config()** (16 connections) — `analysis/pipeline/config.py`
- **pipeline/__main__.py** (8 connections) — `analysis/pipeline/__main__.py`
- **analysis/tests/test_config.py** (7 connections) — `analysis/tests/test_config.py`
- **ConfigError** (5 connections) — `analysis/pipeline/config.py`
- **main()** (5 connections) — `analysis/pipeline/__main__.py`
- **CalibrationEpoch** (4 connections) — `analysis/pipeline/config.py`
- **KeypointsConfig** (4 connections) — `analysis/pipeline/config.py`
- **PathsConfig** (4 connections) — `analysis/pipeline/config.py`
- **build_parser()** (3 connections) — `analysis/pipeline/__main__.py`
- **test_load_config_rejects_empty_views_list()** (3 connections) — `analysis/tests/test_config.py`
- **test_load_config_rejects_missing_top_level_key()** (3 connections) — `analysis/tests/test_config.py`
- **test_load_config_rejects_primary_keypoint_outside_scheme()** (3 connections) — `analysis/tests/test_config.py`
- **test_load_config_has_every_key_and_default()** (2 connections) — `analysis/tests/test_config.py`
- **Path** (1 connections)
- **ValueError** (1 connections)
- **ArgumentParser** (1 connections)
- **Loads and validates config.toml into typed dataclasses. Every threshold, path,…** (1 connections) — `analysis/pipeline/config.py`
- **config.toml is missing a required key or holds an invalid value.** (1 connections) — `analysis/pipeline/config.py`
- **CLI entry point. python -m pipeline manifest [--config path.toml] [--dry-run]…** (1 connections) — `analysis/pipeline/__main__.py`

## Relationships

- [test_orchestration.py](test_orchestration.py.md) (9 shared connections)
- [orchestration.py](orchestration.py.md) (6 shared connections)
- [test_qc_gate.py](test_qc_gate.py.md) (4 shared connections)
- [test_kinematics.py](test_kinematics.py.md) (4 shared connections)
- [load_config](load_config.md) (3 shared connections)

## Source Files

- `analysis/pipeline/__main__.py`
- `analysis/pipeline/config.py`
- `analysis/tests/test_config.py`

## Audit Trail

- EXTRACTED: 55 (95%)
- INFERRED: 3 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*