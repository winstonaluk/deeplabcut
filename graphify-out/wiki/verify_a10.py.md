# verify_a10.py

> 18 nodes

## Key Concepts

- **verify_a10.py** (21 connections) — `acquisition/tools/verify_a10.py`
- **main()** (12 connections) — `acquisition/tools/verify_a10.py`
- **Report** (7 connections) — `acquisition/tools/verify_a10.py`
- **resolve_encoder()** (7 connections) — `acquisition/acquisition/encoder.py`
- **encoder.py** (6 connections) — `acquisition/acquisition/encoder.py`
- **probe_encoder()** (3 connections) — `acquisition/acquisition/encoder.py`
- **ffprobe()** (3 connections) — `acquisition/tools/verify_a10.py`
- **test_resolve_encoder_falls_back_when_preferred_is_unavailable()** (2 connections) — `acquisition/tests/test_capture_pipeline.py`
- **Path** (2 connections)
- **.check()** (1 connections) — `acquisition/tools/verify_a10.py`
- **.__init__()** (1 connections) — `acquisition/tools/verify_a10.py`
- **.ok()** (1 connections) — `acquisition/tools/verify_a10.py`
- **.render()** (1 connections) — `acquisition/tools/verify_a10.py`
- **FFmpeg encoder capability probing and fallback selection. h264_qsv (Intel Quick…** (1 connections) — `acquisition/acquisition/encoder.py`
- **Runs a throwaway 1-frame encode. Returns True iff it succeeds.** (1 connections) — `acquisition/acquisition/encoder.py`
- **Returns ``preferred`` if it actually works here, else ``fallback``. Never…** (1 connections) — `acquisition/acquisition/encoder.py`
- **Checkpoint A10 verification: record from the real camera and check the result.…** (1 connections) — `acquisition/tools/verify_a10.py`
- **Collects pass/fail lines so one run reports every problem at once.** (1 connections) — `acquisition/tools/verify_a10.py`

## Relationships

- [BoundedFrameQueue](BoundedFrameQueue.md) (8 shared connections)
- [load_config](load_config.md) (3 shared connections)
- [CameraError](CameraError.md) (3 shared connections)
- [SpinnakerCamera](SpinnakerCamera.md) (2 shared connections)
- [test_camera_schema.py](test_camera_schema.py.md) (2 shared connections)
- [Frame](Frame.md) (2 shared connections)
- [WriterThread](WriterThread.md) (2 shared connections)
- [Logging.py](Logging.py.md) (2 shared connections)
- [CameraBackend](CameraBackend.md) (1 shared connections)
- [test_storage_a8.py](test_storage_a8.py.md) (1 shared connections)

## Source Files

- `acquisition/acquisition/encoder.py`
- `acquisition/tests/test_capture_pipeline.py`
- `acquisition/tools/verify_a10.py`

## Audit Trail

- EXTRACTED: 48 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*