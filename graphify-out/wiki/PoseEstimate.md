# PoseEstimate

> 19 nodes

## Key Concepts

- **PoseEstimate** (9 connections) — `acquisition/pose/pose_provider.py`
- **pose_provider.py** (8 connections) — `acquisition/pose/pose_provider.py`
- **NullPoseProvider** (7 connections) — `acquisition/pose/null_pose_provider.py`
- **null_pose_provider.py** (7 connections) — `acquisition/pose/null_pose_provider.py`
- **PoseProvider** (6 connections) — `acquisition/pose/pose_provider.py`
- **TriggerService** (5 connections) — `acquisition/pose/trigger_service.py`
- **trigger_service.py** (5 connections) — `acquisition/pose/trigger_service.py`
- **.infer()** (4 connections) — `acquisition/pose/pose_provider.py`
- **.infer()** (3 connections) — `acquisition/pose/null_pose_provider.py`
- **.on_pose()** (3 connections) — `acquisition/pose/trigger_service.py`
- **test_null_pose_provider_satisfies_protocol_and_returns_none()** (3 connections) — `acquisition/tests/test_interfaces.py`
- **Protocol** (1 connections)
- **The only PoseProvider this app ships. Real inference is out of scope.** (1 connections) — `acquisition/pose/null_pose_provider.py`
- **Always returns None. Satisfies PoseProvider structurally so callers (e.g. a…** (1 connections) — `acquisition/pose/null_pose_provider.py`
- **PoseProvider protocol: the seam for DLC-Live, not implemented yet. Any real-…** (1 connections) — `acquisition/pose/pose_provider.py`
- **One frame's inferred keypoints. Shape TBD by the DLC-Live integration;…** (1 connections) — `acquisition/pose/pose_provider.py`
- **Returns a pose estimate for this frame, or None if unavailable.** (1 connections) — `acquisition/pose/pose_provider.py`
- **Electrophysiology trigger hook. Out of scope -- no-op by design. Kept as a real…** (1 connections) — `acquisition/pose/trigger_service.py`
- **No-op. Electrophysiology trigger logic is out of scope for this app.** (1 connections) — `acquisition/pose/trigger_service.py`

## Relationships

- [test_interfaces.py](test_interfaces.py.md) (8 shared connections)
- [Frame](Frame.md) (6 shared connections)
- [BoundedFrameQueue](BoundedFrameQueue.md) (2 shared connections)

## Source Files

- `acquisition/pose/null_pose_provider.py`
- `acquisition/pose/pose_provider.py`
- `acquisition/pose/trigger_service.py`
- `acquisition/tests/test_interfaces.py`

## Audit Trail

- EXTRACTED: 37 (88%)
- INFERRED: 5 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*