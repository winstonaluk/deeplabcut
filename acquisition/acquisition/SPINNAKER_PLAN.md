# SpinnakerCamera implementation plan

**Checkpoint A10 — implemented.** `spinnaker_camera.py` now drives the real
camera; this document is the record of *why* each step is shaped the way it is,
and the reference for anyone changing it. Verified 2026-08-14: 60 s, 3960
frames, zero drops, zero incomplete, no frame-ID gaps (`tools/verify_a10.py`).

What remains for A10 to pass end to end is rig configuration, not code —
`UserSet1` still holds factory defaults, so the `[camera_verify]` and frame-rate
checks fail. See `HARDWARE.md`.

Rewritten 2026-08-14 against the rig's actual camera rather than against
generic SDK examples — every node name here was confirmed present on the
device. Read `HARDWARE.md` in this directory first: it records what the camera
actually reports, including the parts that contradicted the original design
notes.

## Prerequisites

1. Spinnaker SDK installed (vendor installer, not pip). **Already done** on the
   acquisition PC: 4.3.0.190.
2. The matching PySpin wheel. **Already installed** in the `acquire` conda env:
   `spinnaker_python-4.3.0.190-cp310`. Note PySpin wheels are built per Python
   version and are not forward/backward compatible — this one pins the app to
   Python 3.10, which is why `app/config.py` falls back to the `tomli` backport
   instead of stdlib `tomllib`.
3. numpy **< 2**. PySpin does not support numpy 2.x; `requirements.txt` carries
   the upper bound.
4. Camera connected. It is USB3, not GigE — none of the GigE MTU/jumbo-frame/
   packet-size tuning advice applies, and there is ample link headroom
   (380 MB/s limit against the ~11.7 MB/s we need).

**If every node reads RO**, another Spinnaker session (SpinView, or a script
that exited without `DeInit()`) has the camera's parameters latched. Close it
and try again — see HARDWARE.md, "Resolved: the read-only nodes symptom is a
parameter lock". `load_user_set()` detects this and reports it rather than
raising.

## Reference examples

From the SDK's Python examples, vendored at `docs/PySpinExamples/`:

| Example | Use it for |
|---|---|
| `Acquisition.py` | device enumeration, `AcquisitionMode`, begin/end acquisition |
| `ImageEvents.py` | the `ImageEventHandler` subclass pattern (invariant 3) |
| `ChunkData.py` | `ChunkSelector`/`ChunkEnable` loop, reading chunk data off an image |
| `BufferHandling.py` | `StreamBufferHandlingMode`, `StreamBufferCountManual` |
| `ImageFormatControl.py` | the general enumeration-node get/set pattern |
| `NodeMapInfo.py` | node access-mode inspection when something is unreadable |

**There is no `UserSets.py`** in this SDK's Python examples — the original plan
cited one, but it is a C++-only example. Use the enumeration + command node
pattern from `ImageFormatControl.py` instead.

## System / CameraList lifetime (cross-cutting)

`PySpin.System.GetInstance()` is process-wide, not per-camera. Because the app
is N-camera by construction (invariant 1), `SpinnakerCamera` instances must
**share one `System`** rather than each calling `GetInstance()` — a module-level
lazily created singleton with reference counting, released via
`system.ReleaseInstance()` only when the last camera closes. Releasing while
another camera is still open is a classic PySpin crash.

PySpin also requires `CameraPtr` and `CameraList` to be explicitly `del`'d
before `ReleaseInstance()`; they are not cleaned up by scope exit the way the
C++ objects are.

```python
_system = None
_open_camera_count = 0
_system_lock = threading.Lock()
```

## `open()`

Idempotent — preflight opens the camera and leaves it open on success, and
`CaptureController.start()` then opens it again. A second call must be a no-op.

1. Acquire the shared `System`; `system.GetCameras()` → `PySpin.CameraList`.
2. Find the camera by serial: iterate, read
   `PySpin.CStringPtr(cam.GetTLDeviceNodeMap().GetNode("DeviceSerialNumber")).GetValue()`,
   match against `self._serial`. Not found → `CameraError`, never a raw
   `PySpin.SpinnakerException` (keep PySpin behind the interface).
3. `cam.Init()`.
4. Read and cache what the backend must report about itself:
   - `self._resolution` from the `Width`/`Height` nodes.
   - `self._frame_rate` from `AcquisitionResultingFrameRate` — **not**
     `AcquisitionFrameRate`, which is a ceiling. On the rig camera these read
     66.12 and 199.93 respectively; the first is the truth.
5. Configure chunk data (below).
6. Configure stream buffers (below).
7. Set `AcquisitionMode` to `Continuous`.

### Chunk data

The camera ships with `ChunkModeActive` False and both required chunks
disabled, so **invariant 6 is unsatisfiable unless the app enables them**:

```python
for chunk_name in REQUIRED_CHUNKS:          # ("FrameID", "Timestamp")
    selector.SetIntValue(selector.GetEntryByName(chunk_name).GetValue())
    PySpin.CBooleanPtr(nodemap.GetNode("ChunkEnable")).SetValue(True)
PySpin.CBooleanPtr(nodemap.GetNode("ChunkModeActive")).SetValue(True)
```

Then verify by reading back, and log that the app did it. This is a deliberate,
documented carve-out from invariant 7 — see the invariant 7 note in
`acquisition/CLAUDE.md`. Also read `TimestampIncrement` here and log it: it is
1000 on this camera, meaning the chunk timestamp is already in nanoseconds and
needs no scaling, but that is a per-model property and should not be assumed.

### Stream buffers

From `cam.GetTLStreamNodeMap()` — **not** covered by user sets, so the app owns
these outright:

- `StreamBufferHandlingMode` → `OldestFirst`. Never `NewestOnly`: it drops
  frames silently, which is right for a viewer and wrong for a recorder.
- `StreamBufferCountMode` → `Manual`, then `StreamBufferCountManual` →
  `capture.stream_buffer_count` (64 ≈ 2 s of slack at 30 fps; the camera ships
  with 10 ≈ 0.33 s).

Log the achieved count — the node clamps to its own max.

## `load_user_set(user_set_name)`

1. `nodemap = cam.GetNodeMap()`.
2. Set `UserSetSelector` to `user_set_name` (e.g. `"UserSet1"`).
3. Execute the `UserSetLoad` command node.
4. Return True on success, False on failure. Never raise for a load failure —
   preflight decides whether it blocks.

Check `PySpin.IsWritable()` on the command node before executing and return
False with a clear log line if it is not, rather than letting the
`AccessException` escape as a crash. That is the live failure mode on this
camera today.

## `verify_settings(expected)`

Read-only. For each `node_name, expected_value` in `expected` (which comes from
`config.toml`'s `[camera_verify]`):

1. `node = nodemap.GetNode(node_name)`; if absent or unreadable, that is a
   **failed** `NodeCheck` with actual `"<unreadable>"`, not an exception.
2. Read it as a string: enumerations via
   `CEnumerationPtr(node).GetCurrentEntry().GetSymbolic()`, booleans/integers/
   floats via `str(ptr(node).GetValue())`. The probe script's `read()` helper
   in `tools/probe_camera.py` is the working version of this — reuse its
   pointer-cast cascade.
3. Compare as strings, build the `NodeCheck`.

**Never write a node to make a check pass.** That is what keeps invariant 7
intact: the app refuses to record against a wrongly-configured camera, it does
not silently fix it.

Float-valued nodes compared as strings will be brittle if any are ever added to
`[camera_verify]`. Today the table holds only enumerations and booleans; the
numeric frame-rate check is done separately and numerically by preflight,
against `capture.fps_tolerance`.

## `start_streaming(on_frame)`

Where invariant 3 ("not polling") is earned. Subclass
`PySpin.ImageEventHandler` and override `OnImageEvent(self, image)`:

```python
def OnImageEvent(self, image):
    try:
        if image.IsIncomplete():
            self._incomplete += 1        # own counter; see below
            return
        chunk = image.GetChunkData()
        converted = self._processor.Convert(image, PySpin.PixelFormat_Mono8)
        arr = np.array(converted.GetNDArray(), copy=True)   # see below
        self._on_frame(Frame(
            image=arr,
            hardware_timestamp_ns=int(chunk.GetTimestamp()),
            frame_id=int(chunk.GetFrameID()),
            pixel_format=self._pixel_format,
        ))
    finally:
        image.Release()                  # every path, always
```

Three details, each of which fails quietly if missed:

- **Copy the array.** `GetNDArray()` returns a view onto a buffer the SDK
  recycles at `Release()`. Frames outlive this callback — the pre-roll deque
  holds ~60 and the writer queue up to 120 — so a view would alias data the
  camera has already overwritten. The corruption scales with queue depth and
  looks like a compression artifact. This is the highest-risk line in the file.
- **Release on every path**, including exceptions, or the camera's buffer pool
  is exhausted and acquisition stalls.
- **Count incomplete frames separately** from the writer queue's dropped
  frames. A full queue means the encoder can't keep up; an incomplete image
  means the camera-to-host link dropped data. Different causes, different
  fixes, so they never share a counter — hence
  `CameraBackend.incomplete_frame_count`.

Then `cam.RegisterEventHandler(handler)` and `cam.BeginAcquisition()`. **Keep a
reference to the handler on `self`** — PySpin does not keep the Python object
alive, and a garbage-collected handler silently stops firing.

`ImageProcessor` should be constructed once and held, not per frame.

## `stop_streaming()`

`cam.EndAcquisition()`, then `cam.UnregisterEventHandler(handler)`. Order
matters — unregistering before ending acquisition has caused crashes in past
Spinnaker versions. Idempotent when not streaming.

## `close()`

`cam.DeInit()`, `del self._camera`, then `cam_list.Clear()`, then decrement the
shared open-camera count and call `system.ReleaseInstance()` only at zero.
Idempotent.

## Error handling convention

Every public method wraps its PySpin calls:

```python
try:
    ...
except PySpin.SpinnakerException as exc:
    raise CameraError(str(exc)) from exc
```

so callers (preflight, `CaptureController`) never import or catch
PySpin-specific exceptions.

`import PySpin` stays **inside** methods, never at module scope, so this module
remains importable — and `python -m app --mock` remains runnable — on a machine
with no SDK (invariant 2).

## Threading contract (unchanged)

`OnImageEvent` runs on a Spinnaker-internal thread, which *is* the "not
polling" requirement. `on_frame` executes on that thread, exactly as
`MockCamera`'s background thread does today, so `CaptureController` and the
bounded queue need no changes for either backend.

## Testing

The suite must still pass with the camera unplugged (invariant 2). So:

- Everything provable without hardware is already tested against `MockCamera`
  in `tests/test_camera_schema.py` — the schema, the preflight comparisons, the
  writer's geometry guard.
- Hardware tests go behind a `@pytest.mark.hardware` marker, deselected by
  default, in the same shape as the existing `requires_ffmpeg` marker in
  `tests/conftest.py`.

**A10 is done when** a 60-second recording against the real camera produces a
playable file at the configured rate, with a timestamp sidecar whose hardware
timestamps increase monotonically, whose frame IDs have no gaps, and with zero
incomplete frames.
