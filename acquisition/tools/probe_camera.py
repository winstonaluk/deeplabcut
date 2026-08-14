"""Probe of the attached FLIR camera.

    python tools/probe_camera.py                 # read-only
    python tools/probe_camera.py --dump-user-sets  # also loads each user set

Run this on the acquisition PC after any firmware change, camera swap, or
SpinView reconfiguration, and update `acquisition/HARDWARE.md` with what it
prints. HARDWARE.md is the record of what the camera actually is; this script
is how that record gets made, and it is committed so the readings stay
reproducible by anyone at the rig.

Requires PySpin, so it is deliberately outside the package and outside the
test suite -- nothing here runs in CI or on a machine with no camera.

**If everything looks read-only, something else has the camera.** A live
Spinnaker session -- SpinView left open, or a crashed script -- latches the
camera's parameters, and FLIR then reports PixelFormat, Width, Height,
UserSetLoad and UserSetSave as RO *as a group*. That is not a camera fault and
not an empty user set; close the other application and probe again. The ACCESS
MODES section below exists to make that diagnosis in one glance.

By default this writes nothing except ChunkSelector, which it steps through to
read back which chunks are enabled and then restores. `--dump-user-sets` is the
exception: it executes UserSetLoad for each set to report its contents, which
changes live camera settings. It never executes UserSetSave, and it reloads
UserSetDefault at the end so the camera is left as it boots.
"""
import sys

import PySpin

DUMP_USER_SETS = "--dump-user-sets" in sys.argv

# Read back after a user set loads; these are the settings that decide whether
# footage is usable as DLC training data (see config.toml [camera_verify]).
USER_SET_FEATURES = (
    "PixelFormat", "Width", "Height", "OffsetX", "OffsetY",
    "ExposureAuto", "ExposureTime", "GainAuto", "Gain",
    "GammaEnable", "Gamma", "BlackLevel", "AdcBitDepth",
    "AcquisitionFrameRateEnable", "AcquisitionFrameRate",
    "AcquisitionResultingFrameRate", "TriggerMode",
    "SensorShutterMode", "ChunkModeActive",
)

ACCESS_MODE_NAMES = {0: "NI", 1: "NA", 2: "WO", 3: "RO", 4: "RW"}

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

print("\n=== ACCESS MODES ===")
print("  (all RO together => another application has the camera latched)")
for k in ("UserSetLoad", "UserSetSave", "UserSetSelector", "UserSetDefault",
          "PixelFormat", "Width", "Height", "ExposureAuto", "GainAuto",
          "AcquisitionFrameRateEnable", "ChunkModeActive", "TLParamsLocked"):
    node = nm.GetNode(k)
    if node is None:
        print(f"  {k:28s} <absent>")
        continue
    mode = node.GetAccessMode()
    print(f"  {k:28s} {ACCESS_MODE_NAMES.get(mode, mode)}")


def load_user_set(nodemap, name):
    """Executes UserSetLoad for `name`. Returns None on success, else why not."""
    sel = PySpin.CEnumerationPtr(nodemap.GetNode("UserSetSelector"))
    if not PySpin.IsWritable(sel):
        return "UserSetSelector not writable"
    entry = sel.GetEntryByName(name)
    if entry is None or not PySpin.IsReadable(PySpin.CEnumEntryPtr(entry)):
        return f"no such user set: {name}"
    sel.SetIntValue(PySpin.CEnumEntryPtr(entry).GetValue())
    cmd = PySpin.CCommandPtr(nodemap.GetNode("UserSetLoad"))
    if not PySpin.IsWritable(cmd):
        return "UserSetLoad not writable (another application may have the camera)"
    try:
        cmd.Execute()
    except PySpin.SpinnakerException as exc:
        return str(exc)
    return None


if DUMP_USER_SETS:
    print("\n=== USER SET CONTENTS ===")
    print("  (loads each set; live camera settings change, restored at the end)")
    boot_set = s(nm, "UserSetDefault")
    for user_set in ("Default", "UserSet0", "UserSet1"):
        print(f"\n  --- after UserSetLoad({user_set}) ---")
        failure = load_user_set(nm, user_set)
        if failure is not None:
            print(f"    load failed: {failure}")
            continue
        for k in USER_SET_FEATURES:
            print(f"    {k}: {s(nm, k)}")

    # Leave the camera in the state it powers up in, whatever that is.
    print(f"\n  restoring boot state: UserSetLoad({boot_set})")
    failure = load_user_set(nm, str(boot_set))
    if failure is not None:
        print(f"    restore failed: {failure}")
else:
    print("\n(pass --dump-user-sets to also report what each user set contains)")

cam.DeInit()
del cam
cl.Clear()
system.ReleaseInstance()
