"""Read-only probe of the attached FLIR camera. Writes nothing to the camera.

    python tools/probe_camera.py

Run this on the acquisition PC after any firmware change, camera swap, or
SpinView reconfiguration, and update `acquisition/HARDWARE.md` with what it
prints. HARDWARE.md is the record of what the camera actually is; this script
is how that record gets made, and it is committed so the readings stay
reproducible by anyone at the rig.

Requires PySpin, so it is deliberately outside the package and outside the
test suite -- nothing here runs in CI or on a machine with no camera.

The one node this touches is ChunkSelector, which it iterates to read back
which chunks are enabled and then restores to its original value. It never
executes UserSetLoad or UserSetSave.
"""
import PySpin

def s(nodemap, name):
    n = nodemap.GetNode(name)
    if n is None:
        return "<absent>"
    for ptr in (PySpin.CStringPtr, PySpin.CEnumerationPtr, PySpin.CIntegerPtr,
                PySpin.CFloatPtr, PySpin.CBooleanPtr):
        try:
            p = ptr(n)
            if not PySpin.IsReadable(p):
                continue
            if ptr is PySpin.CEnumerationPtr:
                return p.GetCurrentEntry().GetSymbolic()
            return p.GetValue()
        except Exception:
            continue
    return "<unreadable>"

def entries(nodemap, name):
    n = nodemap.GetNode(name)
    if n is None:
        return "<absent>"
    try:
        e = PySpin.CEnumerationPtr(n)
        return [PySpin.CEnumEntryPtr(x).GetSymbolic() for x in e.GetEntries()
                if PySpin.IsReadable(PySpin.CEnumEntryPtr(x))]
    except Exception as ex:
        return f"<err {ex}>"

system = PySpin.System.GetInstance()
cl = system.GetCameras()
cam = cl[0]
cam.Init()
nm = cam.GetNodeMap()
tl = cam.GetTLDeviceNodeMap()
sm = cam.GetTLStreamNodeMap()

print("=== DEVICE ===")
for k in ("DeviceModelName", "DeviceSerialNumber", "DeviceVersion",
          "DeviceFirmwareVersion", "DeviceCurrentSpeed", "DeviceType"):
    print(f"  {k}: {s(tl, k)}")

print("\n=== SENSOR / FORMAT ===")
for k in ("SensorWidth", "SensorHeight", "WidthMax", "HeightMax", "Width", "Height",
          "OffsetX", "OffsetY", "PixelFormat", "PixelColorFilter", "PixelSize",
          "BinningHorizontal", "BinningVertical", "AdcBitDepth", "ReverseX", "ReverseY"):
    print(f"  {k}: {s(nm, k)}")
print(f"  PixelFormat entries: {entries(nm, 'PixelFormat')}")

print("\n=== ACQUISITION ===")
for k in ("AcquisitionMode", "AcquisitionFrameRateEnable", "AcquisitionFrameRate",
          "AcquisitionResultingFrameRate", "ExposureAuto", "ExposureMode", "ExposureTime",
          "GainAuto", "Gain", "GammaEnable", "Gamma", "BlackLevel",
          "TriggerMode", "TriggerSource", "TriggerSelector",
          "DeviceLinkThroughputLimit", "DeviceLinkCurrentThroughput",
          "DeviceMaxThroughput", "SensorShutterMode"):
    print(f"  {k}: {s(nm, k)}")

print("\n=== USER SETS ===")
print(f"  UserSetSelector entries: {entries(nm, 'UserSetSelector')}")
print(f"  UserSetSelector current: {s(nm, 'UserSetSelector')}")
print(f"  UserSetDefault: {s(nm, 'UserSetDefault')}")
print(f"  UserSetFeatureEnable: {s(nm, 'UserSetFeatureEnable')}")

print("\n=== CHUNK ===")
print(f"  ChunkModeActive: {s(nm, 'ChunkModeActive')}")
print(f"  ChunkSelector entries: {entries(nm, 'ChunkSelector')}")
print(f"  ChunkSelector current: {s(nm, 'ChunkSelector')}")
# which chunks are currently enabled
csel = PySpin.CEnumerationPtr(nm.GetNode("ChunkSelector"))
cen = PySpin.CBooleanPtr(nm.GetNode("ChunkEnable"))
enabled = {}
if PySpin.IsReadable(csel):
    original = csel.GetIntValue()
    for e in csel.GetEntries():
        ee = PySpin.CEnumEntryPtr(e)
        if not PySpin.IsReadable(ee):
            continue
        try:
            csel.SetIntValue(ee.GetValue())
            enabled[ee.GetSymbolic()] = bool(cen.GetValue()) if PySpin.IsReadable(cen) else None
        except Exception:
            enabled[ee.GetSymbolic()] = "<err>"
    csel.SetIntValue(original)  # restore
print(f"  ChunkEnable state: {enabled}")

print("\n=== TIMESTAMP ===")
for k in ("TimestampLatchValue", "Timestamp", "TimestampIncrement"):
    print(f"  {k}: {s(nm, k)}")

print("\n=== STREAM (TL) ===")
for k in ("StreamBufferHandlingMode", "StreamBufferCountMode", "StreamBufferCountManual",
          "StreamBufferCountResult", "StreamMode", "StreamDefaultBufferCount"):
    print(f"  {k}: {s(sm, k)}")
print(f"  StreamBufferHandlingMode entries: {entries(sm, 'StreamBufferHandlingMode')}")
n = sm.GetNode("StreamBufferCountManual")
if n is not None:
    try:
        p = PySpin.CIntegerPtr(n)
        print(f"  StreamBufferCountManual min/max: {p.GetMin()}/{p.GetMax()}")
    except Exception as ex:
        print(f"  buffer count range err: {ex}")

cam.DeInit()
del cam
cl.Clear()
system.ReleaseInstance()
