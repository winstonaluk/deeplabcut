# test_kinematics.py

> 65 nodes

## Key Concepts

- **test_kinematics.py** (46 connections) — `analysis/tests/test_kinematics.py`
- **kinematics.py** (28 connections) — `analysis/pipeline/stages/kinematics.py`
- **compute_trial_kinematics()** (22 connections) — `analysis/pipeline/stages/kinematics.py`
- **ndarray** (16 connections)
- **CalibrationRecord** (9 connections) — `analysis/pipeline/contracts.py`
- **interpolate_gaps()** (9 connections) — `analysis/pipeline/stages/kinematics.py`
- **smooth()** (9 connections) — `analysis/pipeline/stages/kinematics.py`
- **KinematicsConfig** (8 connections) — `analysis/pipeline/config.py`
- **compute_pole_frame()** (8 connections) — `analysis/pipeline/stages/kinematics.py`
- **pole_landmark_drift_flagged()** (8 connections) — `analysis/pipeline/stages/kinematics.py`
- **height_fraction()** (7 connections) — `analysis/pipeline/stages/kinematics.py`
- **undistort_points()** (7 connections) — `analysis/pipeline/stages/kinematics.py`
- **PoleFrame** (6 connections) — `analysis/pipeline/stages/kinematics.py`
- **apply_likelihood_filter()** (6 connections) — `analysis/pipeline/stages/kinematics.py`
- **_build_synthetic_constant_velocity_descent()** (6 connections) — `analysis/tests/test_kinematics.py`
- **compute_velocity()** (5 connections) — `analysis/pipeline/stages/kinematics.py`
- **detect_descent_threshold_crossing()** (5 connections) — `analysis/pipeline/stages/kinematics.py`
- **occlusion_fraction()** (5 connections) — `analysis/pipeline/stages/kinematics.py`
- **perpendicular_offset_mm()** (5 connections) — `analysis/pipeline/stages/kinematics.py`
- **scale_to_mm()** (5 connections) — `analysis/pipeline/stages/kinematics.py`
- **to_kinematics_long_rows()** (5 connections) — `analysis/pipeline/stages/kinematics.py`
- **to_trial_summary_row()** (5 connections) — `analysis/pipeline/stages/kinematics.py`
- **velocity_by_height()** (5 connections) — `analysis/pipeline/stages/kinematics.py`
- **test_trial_summary_and_kinematics_long_rows_are_consistent()** (5 connections) — `analysis/tests/test_kinematics.py`
- **TrialKinematicsResult** (4 connections) — `analysis/pipeline/stages/kinematics.py`
- *... and 40 more nodes in this community*

## Relationships

- [test_stages_b7_scaffold.py](test_stages_b7_scaffold.py.md) (5 shared connections)
- [pipeline/config.py](pipeline-config.py.md) (4 shared connections)
- [test_report.py](test_report.py.md) (4 shared connections)
- [test_orchestration.py](test_orchestration.py.md) (2 shared connections)

## Source Files

- `analysis/pipeline/config.py`
- `analysis/pipeline/contracts.py`
- `analysis/pipeline/stages/kinematics.py`
- `analysis/tests/test_kinematics.py`

## Audit Trail

- EXTRACTED: 165 (98%)
- INFERRED: 3 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*