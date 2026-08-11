"""Stage 8: kinematics -- the pipeline's product, y(t).

Pure functions composed in the order analysis/CLAUDE.md specifies:
likelihood filter -> gap interpolation (max_gap_frames; longer gaps stay
NaN, never silently bridged) -> temporal smoothing -> undistort coordinates
-> pole-landmark coordinate frame -> normalise height to fraction of pole
length -> scale to mm -> descent rule -> y(t), v(t), velocity-by-height.

Operates on already-loaded pose arrays (numpy), decoupled from DLC's .h5
file format -- loading real pose output belongs to stage 7 (B7 scaffold).
This is what B4 asks for: the pure pipeline as testable functions, proven
against synthetic pose arrays with known ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
import pandas as pd

from pipeline.config import KinematicsConfig
from pipeline.contracts import CalibrationRecord, KinematicsLongRow, TrialSummaryRow

STAGE_VERSION = "1.0.0"


# -- step 1: likelihood filter --

def apply_likelihood_filter(
    x: np.ndarray, y: np.ndarray, likelihood: np.ndarray, cutoff: float
) -> tuple[np.ndarray, np.ndarray]:
    """Sets x, y to NaN wherever likelihood < cutoff."""
    x = x.astype(float).copy()
    y = y.astype(float).copy()
    below = likelihood < cutoff
    x[below] = np.nan
    y[below] = np.nan
    return x, y


# -- step 2: gap interpolation --

def interpolate_gaps(arr: np.ndarray, max_gap_frames: int) -> np.ndarray:
    """Linearly interpolates interior NaN runs of length <= max_gap_frames.
    Longer runs, and runs touching either edge (no bracketing valid value
    to interpolate from), stay NaN -- never silently bridged."""
    arr = arr.astype(float).copy()
    n = len(arr)
    is_nan = np.isnan(arr)
    i = 0
    while i < n:
        if not is_nan[i]:
            i += 1
            continue
        start = i
        while i < n and is_nan[i]:
            i += 1
        end = i  # exclusive
        gap_len = end - start
        if start == 0 or end == n:
            continue  # edge gap: no bracketing value, stays NaN
        if gap_len <= max_gap_frames:
            left_val = arr[start - 1]
            right_val = arr[end]
            arr[start:end] = np.linspace(left_val, right_val, gap_len + 2)[1:-1]
    return arr


# -- step 3: temporal smoothing --

def smooth(arr: np.ndarray, method: str, window: int) -> np.ndarray:
    """Median (pandas rolling) or Savitzky-Golay (scipy, per contiguous
    valid segment). Positions still NaN after gap interpolation stay NaN --
    smoothing must never fabricate a value at an unfilled gap."""
    if method == "median":
        smoothed = pd.Series(arr).rolling(window, center=True, min_periods=1).median().to_numpy()
    elif method == "savgol":
        smoothed = _savgol_per_segment(arr, window)
    else:
        raise ValueError(f"unknown smoothing method: {method!r}")
    smoothed = smoothed.copy()
    smoothed[np.isnan(arr)] = np.nan
    return smoothed


def _savgol_per_segment(arr: np.ndarray, window: int) -> np.ndarray:
    from scipy.signal import savgol_filter

    result = arr.astype(float).copy()
    n = len(arr)
    is_nan = np.isnan(arr)
    win = window if window % 2 == 1 else window - 1
    polyorder = min(3, win - 1)
    i = 0
    while i < n:
        if is_nan[i]:
            i += 1
            continue
        start = i
        while i < n and not is_nan[i]:
            i += 1
        end = i
        if end - start >= win:
            result[start:end] = savgol_filter(arr[start:end], win, polyorder)
        # shorter segments can't be smoothed with this window; left as-is
    return result


# -- step 4: undistort coordinates (never re-encode video, invariant 2) --

def undistort_points(
    x: np.ndarray, y: np.ndarray, calibration: CalibrationRecord
) -> tuple[np.ndarray, np.ndarray]:
    x_out = np.full_like(np.asarray(x, dtype=float), np.nan)
    y_out = np.full_like(np.asarray(y, dtype=float), np.nan)
    valid = ~(np.isnan(x) | np.isnan(y))
    if not valid.any():
        return x_out, y_out

    camera_matrix = np.array(calibration.camera_matrix, dtype=float)
    dist_coeffs = np.array(calibration.distortion_coefficients, dtype=float)
    points = np.stack([np.asarray(x)[valid], np.asarray(y)[valid]], axis=1).reshape(-1, 1, 2).astype(float)
    undistorted = cv2.undistortPoints(points, camera_matrix, dist_coeffs, P=camera_matrix).reshape(-1, 2)
    x_out[valid] = undistorted[:, 0]
    y_out[valid] = undistorted[:, 1]
    return x_out, y_out


# -- pole-landmark coordinate frame --

@dataclass(frozen=True)
class PoleFrame:
    base_xy: tuple[float, float]
    top_xy: tuple[float, float]
    pixel_length: float


def compute_pole_frame(
    pole_top_x: np.ndarray, pole_top_y: np.ndarray, pole_base_x: np.ndarray, pole_base_y: np.ndarray
) -> PoleFrame:
    """Pole landmarks are static; the per-trial frame uses the median
    position across valid frames, robust to per-frame labeling noise."""
    top = (float(np.nanmedian(pole_top_x)), float(np.nanmedian(pole_top_y)))
    base = (float(np.nanmedian(pole_base_x)), float(np.nanmedian(pole_base_y)))
    length = float(np.hypot(top[0] - base[0], top[1] - base[1]))
    return PoleFrame(base_xy=base, top_xy=top, pixel_length=length)


def height_fraction(x: np.ndarray, y: np.ndarray, pole_frame: PoleFrame) -> np.ndarray:
    """Projects (x, y) onto the base->top axis: 0.0 at base, 1.0 at top.
    Not clipped -- values outside [0, 1] are legitimate near the endpoints,
    and clipping would hide labeling/QC problems instead of surfacing them."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if pole_frame.pixel_length == 0:
        return np.full_like(x, np.nan)
    dx = pole_frame.top_xy[0] - pole_frame.base_xy[0]
    dy = pole_frame.top_xy[1] - pole_frame.base_xy[1]
    px = x - pole_frame.base_xy[0]
    py = y - pole_frame.base_xy[1]
    return (px * dx + py * dy) / (pole_frame.pixel_length ** 2)


def perpendicular_offset_mm(x: np.ndarray, y: np.ndarray, pole_frame: PoleFrame, pole_length_mm: float) -> np.ndarray:
    """Signed distance from the pole axis, in mm. Not the pipeline's primary
    product (y(t) is), but keeps kinematics_long a complete 2D record."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if pole_frame.pixel_length == 0:
        return np.full_like(x, np.nan)
    dx = pole_frame.top_xy[0] - pole_frame.base_xy[0]
    dy = pole_frame.top_xy[1] - pole_frame.base_xy[1]
    perp_x, perp_y = -dy / pole_frame.pixel_length, dx / pole_frame.pixel_length
    px = x - pole_frame.base_xy[0]
    py = y - pole_frame.base_xy[1]
    offset_px = px * perp_x + py * perp_y
    return offset_px * (pole_length_mm / pole_frame.pixel_length)


def scale_to_mm(height_frac: np.ndarray, pole_length_mm: float) -> np.ndarray:
    return np.asarray(height_frac, dtype=float) * pole_length_mm


def pole_landmark_drift_flagged(
    pole_top_x: np.ndarray, pole_top_y: np.ndarray, pole_base_x: np.ndarray, pole_base_y: np.ndarray,
    pole_length_mm: float, threshold_mm: float,
) -> bool:
    """True if either landmark strays beyond threshold_mm from its median
    position at any frame -- the camera was likely bumped mid-trial."""
    frame = compute_pole_frame(pole_top_x, pole_top_y, pole_base_x, pole_base_y)
    if frame.pixel_length == 0:
        return False
    mm_per_px = pole_length_mm / frame.pixel_length
    top_dev = np.hypot(pole_top_x - frame.top_xy[0], pole_top_y - frame.top_xy[1]) * mm_per_px
    base_dev = np.hypot(pole_base_x - frame.base_xy[0], pole_base_y - frame.base_xy[1]) * mm_per_px
    all_dev = np.concatenate([top_dev, base_dev])
    if np.all(np.isnan(all_dev)):
        return False
    return bool(np.nanmax(all_dev) > threshold_mm)


# -- velocity --

def compute_velocity(height_mm: np.ndarray, fps: float) -> np.ndarray:
    return np.gradient(height_mm, 1.0 / fps)


def velocity_by_height(height_frac: np.ndarray, velocity_mm_s: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    valid = ~np.isnan(height_frac) & ~np.isnan(velocity_mm_s)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_idx = np.clip(np.digitize(height_frac[valid], bins) - 1, 0, n_bins - 1) if valid.any() else np.array([], dtype=int)
    valid_velocity = velocity_mm_s[valid]

    rows = []
    for b in range(n_bins):
        mask = bin_idx == b
        vals = valid_velocity[mask]
        rows.append(
            {
                "height_bin_low": bins[b],
                "height_bin_high": bins[b + 1],
                "mean_velocity_mm_s": float(np.mean(vals)) if len(vals) else float("nan"),
                "n_samples": int(mask.sum()),
            }
        )
    return pd.DataFrame(rows)


# -- descent rule (named + versioned, invariant 7) --

def detect_descent_threshold_crossing(
    height_frac: np.ndarray, onset_fraction: float, offset_fraction: float
) -> tuple[int | None, int | None]:
    onset_idx = None
    for i, h in enumerate(height_frac):
        if not np.isnan(h) and h <= onset_fraction:
            onset_idx = i
            break
    if onset_idx is None:
        return None, None

    offset_idx = None
    for i in range(onset_idx, len(height_frac)):
        h = height_frac[i]
        if not np.isnan(h) and h <= offset_fraction:
            offset_idx = i
            break
    return onset_idx, offset_idx


DESCENT_RULES = {
    "threshold_crossing_v1": detect_descent_threshold_crossing,
}


def detect_descent(height_frac: np.ndarray, config: KinematicsConfig) -> tuple[int | None, int | None]:
    rule = DESCENT_RULES.get(config.descent_rule_name)
    if rule is None:
        raise ValueError(f"unknown descent rule: {config.descent_rule_name!r}")
    return rule(height_frac, config.descent_rule_onset_height_fraction, config.descent_rule_offset_height_fraction)


def occlusion_fraction(likelihood: np.ndarray, cutoff: float) -> float:
    return float(np.mean(likelihood < cutoff))


# -- orchestration --

@dataclass(frozen=True)
class TrialKinematicsResult:
    height_mm: np.ndarray  # y(t) -- the pipeline's product
    perpendicular_mm: np.ndarray
    velocity_mm_s: np.ndarray  # v(t)
    likelihood: np.ndarray
    is_interpolated: np.ndarray
    descent_onset_frame: int | None
    descent_offset_frame: int | None
    descent_duration_s: float | None
    mean_velocity_mm_s: float | None
    occlusion_fraction: float
    pole_landmark_drift_flagged: bool


def compute_trial_kinematics(
    x: np.ndarray,
    y: np.ndarray,
    likelihood: np.ndarray,
    pole_top_x: np.ndarray,
    pole_top_y: np.ndarray,
    pole_base_x: np.ndarray,
    pole_base_y: np.ndarray,
    calibration: CalibrationRecord,
    config: KinematicsConfig,
    pole_length_mm: float,
    fps: float,
) -> TrialKinematicsResult:
    x_f, y_f = apply_likelihood_filter(x, y, likelihood, config.likelihood_cutoff)
    nan_before_interp = np.isnan(x_f)

    x_i = interpolate_gaps(x_f, config.max_gap_frames)
    y_i = interpolate_gaps(y_f, config.max_gap_frames)
    is_interpolated = nan_before_interp & ~np.isnan(x_i)

    x_s = smooth(x_i, config.smoothing_method, config.smoothing_window)
    y_s = smooth(y_i, config.smoothing_method, config.smoothing_window)

    x_u, y_u = undistort_points(x_s, y_s, calibration)
    pole_top_u_x, pole_top_u_y = undistort_points(pole_top_x, pole_top_y, calibration)
    pole_base_u_x, pole_base_u_y = undistort_points(pole_base_x, pole_base_y, calibration)
    pole_frame = compute_pole_frame(pole_top_u_x, pole_top_u_y, pole_base_u_x, pole_base_u_y)

    frac = height_fraction(x_u, y_u, pole_frame)
    height_mm = scale_to_mm(frac, pole_length_mm)
    perpendicular_mm = perpendicular_offset_mm(x_u, y_u, pole_frame, pole_length_mm)
    velocity_mm_s = compute_velocity(height_mm, fps)

    onset, offset = detect_descent(frac, config)
    duration_s = (offset - onset) / fps if (onset is not None and offset is not None) else None
    mean_velocity = None
    if onset is not None and offset is not None and offset > onset:
        mean_velocity = float(np.nanmean(np.abs(velocity_mm_s[onset:offset])))

    drift_flagged = pole_landmark_drift_flagged(
        pole_top_x, pole_top_y, pole_base_x, pole_base_y, pole_length_mm,
        config.pole_landmark_drift_threshold_mm,
    )

    return TrialKinematicsResult(
        height_mm=height_mm,
        perpendicular_mm=perpendicular_mm,
        velocity_mm_s=velocity_mm_s,
        likelihood=np.asarray(likelihood, dtype=float),
        is_interpolated=is_interpolated,
        descent_onset_frame=onset,
        descent_offset_frame=offset,
        descent_duration_s=duration_s,
        mean_velocity_mm_s=mean_velocity,
        occlusion_fraction=occlusion_fraction(likelihood, config.likelihood_cutoff),
        pole_landmark_drift_flagged=drift_flagged,
    )


def to_trial_summary_row(trial_uid: str, primary_keypoint: str, result: TrialKinematicsResult) -> TrialSummaryRow:
    return TrialSummaryRow(
        trial_uid=trial_uid,
        primary_keypoint=primary_keypoint,
        descent_onset_frame=result.descent_onset_frame,
        descent_offset_frame=result.descent_offset_frame,
        descent_duration_s=result.descent_duration_s,
        mean_velocity_mm_s=result.mean_velocity_mm_s,
        occlusion_fraction=result.occlusion_fraction,
        pole_landmark_drift_flagged=result.pole_landmark_drift_flagged,
    )


def to_kinematics_long_rows(
    trial_uid: str, view: str, keypoint: str, result: TrialKinematicsResult
) -> list[KinematicsLongRow]:
    return [
        KinematicsLongRow(
            trial_uid=trial_uid,
            view=view,
            keypoint=keypoint,
            frame_index=i,
            x_mm=float(result.perpendicular_mm[i]),
            y_mm=float(result.height_mm[i]),
            likelihood=float(result.likelihood[i]),
            is_interpolated=bool(result.is_interpolated[i]),
        )
        for i in range(len(result.height_mm))
    ]
