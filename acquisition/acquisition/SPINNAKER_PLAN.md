# SpinnakerCamera implementation plan

**Not buildable unattended (checkpoint A9).** Requires the Spinnaker SDK, a
matching PySpin wheel, and a physically connected FLIR camera -- none of
which exist in this environment. `spinnaker_camera.py` scaffolds the class
against `CameraBackend` with `NotImplementedError` bodies; this document is
the plan for filling them in once hardware is available.

References below are to the standard example scripts shipped in the
Spinnaker SDK's `src/` (C++) / `Python3/examples/` directory --
`Acquisition.py`, `ImageEvents.py` (sometimes named `Callback.py` depending
on SDK version), `UserSets.py`, `ChunkData.py`, `NodeMapInfo.py`. Verify
exact filenames against whatever SDK version ships with the lab's camera,
since Teledyne renames/reorganizes these occasionally between releases.

## Prerequisites

1. Install the Spinnaker SDK (vendor installer, not pip).
2. Install the matching PySpin wheel from the SDK's `python/` subdirectory
   for the exact Python version and OS in use -- PySpin wheels are built
   per-Python-version and are not forward/backward compatible.
3. Camera physically connected (GigE or USB3 depending on model). For GigE,
   confirm jumbo frames / firewall exceptions per Teledyne's network
   configuration guide -- dropped frames on a GigE camera are very often a
   network MTU/driver issue, not an application bug.

## System / CameraList lifetime (cross-cutting -- affects all methods)

`PySpin.System.GetInstance()` is process-wide, not per-camera. Because this
app is N-camera by construction (invariant 1), `SpinnakerCamera` instances
must **share one `System` instance** rather than each calling
`GetInstance()` independently -- pattern this as a module-level lazily
created singleton with reference counting, released via
`system.ReleaseInstance()` only when the last camera closes. Getting this
wrong (releasing while another camera is still open) is a classic PySpin
crash source.

```python
# sketch, not final:
_system: PySpin.System | None = None
_open_camera_count = 0
```

## `open()`

1. Acquire the shared `System` (see above); `system.GetCameras()` ->
   `PySpin.CameraList`.
2. Find the target camera by serial: iterate the list, read
   `cam.TLDevice.DeviceSerialNumber.GetValue()` per `Acquisition.py`'s
   device enumeration pattern, match against `self._serial`.
3. If not found: raise `CameraError` (do not raise `PySpin.SpinnakerException`
   directly -- keep PySpin as an implementation detail behind the
   `CameraBackend` interface, same as `CameraError` already does for the
   mock path's error surface).
4. `cam.Init()`. Wrap in `try/except PySpin.SpinnakerException as exc: raise
   CameraError(str(exc)) from exc` -- every PySpin call below should follow
   this same wrapping convention.

## `load_user_set(user_set_name)`

Per `UserSets.py`:

1. `nodemap = cam.GetNodeMap()`.
2. Get the `UserSetSelector` enumeration node, set it to `user_set_name`
   (e.g. `"UserSet1"`).
3. Execute the `UserSetLoad` command node.
4. **Verification is the open question here.** PySpin has no single
   "did it load correctly" call -- verification means re-reading specific
   node values after load and comparing against what `UserSet1` is expected
   to contain (exposure mode, gain, ROI, etc., per SpinView). That expected
   set of values is lab/rig-specific and unknown to this scaffold.
   `# TODO(QUESTIONS.md): a9-userset-verification` -- when hardware is
   available, log the chosen verification strategy (e.g. "check
   `ExposureAuto` reads `Off`" or similar) to `QUESTIONS.md` rather than
   guessing here.

## `start_streaming(on_frame)`

This is where invariant 3 ("not polling") is actually earned:

1. Subclass `PySpin.ImageEventHandler`, override `OnImageEvent(self, image)`.
   Inside the handler:
   - Pull chunk data: `chunk_data = image.GetChunkData()`;
     `chunk_data.GetTimestamp()` for the hardware timestamp,
     `chunk_data.GetFrameID()` for the frame ID -- this is what invariant 6
     ("hardware timestamps only") requires; never substitute
     `time.time()`/`datetime.now()` here.
   - Convert pixel format if needed via `PySpin.ImageProcessor().Convert(image,
     PySpin.PixelFormat_Mono8)` (matches `MockCamera`'s Mono8 frames).
   - `image.GetNDArray()` for the numpy array.
   - Build our `Frame(image=..., hardware_timestamp_ns=..., frame_id=...)`
     and call the injected `on_frame` callback -- same contract
     `MockCamera` already provides, so `CaptureController` needs no changes.
   - **Must call `image.Release()`** before returning, every time, even on
     an error path -- omitting this exhausts the camera's buffer pool and
     is the single most common PySpin bug per `ImageEvents.py`'s comments.
2. `cam.RegisterEventHandler(handler)`, then `cam.BeginAcquisition()`.
3. Keep a reference to the handler instance on `self` -- PySpin does not
   keep the Python object alive on its own, and a garbage-collected handler
   silently stops firing.

## `stop_streaming()`

`cam.EndAcquisition()`, then `cam.UnregisterEventHandler(handler)`. Order
matters: unregistering before ending acquisition has caused crashes in past
Spinnaker versions per community reports -- confirm against the SDK version
actually in use.

## `close()`

`cam.DeInit()`, drop the Python reference to `cam` (`del self._cam`) before
`cam_list.Clear()`, then decrement the shared open-camera count and call
`system.ReleaseInstance()` only when it reaches zero (see System lifetime
note above).

## Error handling convention

Every public method wraps its PySpin calls:

```python
try:
    ...
except PySpin.SpinnakerException as exc:
    raise CameraError(str(exc)) from exc
```

so `CameraBackend` callers (preflight, CaptureController) never need to
import or catch PySpin-specific exceptions.

## Threading contract (unchanged from MockCamera)

`OnImageEvent` runs on a Spinnaker-internal thread already -- this *is* the
"not polling" requirement from invariant 3. `on_frame` executes on that
thread, exactly like `MockCamera`'s background thread today.
`CaptureController.attach_sink()` / the bounded queue handle the handoff to
the writer thread identically regardless of which `CameraBackend`
implementation is feeding them; no changes needed there when this scaffold
is filled in.

## Known open questions to log when hardware work resumes

- `UserSet1` verification strategy (see above).
- Confirm the camera's native pixel format is actually Mono8 (assumed
  throughout this app per acquisition/CLAUDE.md's "720p60, global shutter"
  hardware note, but not yet confirmed against the specific sensor).
- GigE vs USB3 interface-specific buffer/packet-size tuning if dropped
  frames appear at 30fps 720p that MockCamera's software-only path can't
  reproduce.
