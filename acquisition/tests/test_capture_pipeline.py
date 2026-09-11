"""Checkpoint A2: MockCamera -> capture controller -> bounded queue -> writer
-> playable H.264 file, with drop-on-full backpressure and bounded memory."""

from __future__ import annotations

import json
import subprocess
import time

import pytest
import tracemalloc
from pathlib import Path

import numpy as np

from acquisition.capture_controller import CaptureController
from acquisition.encoder import resolve_encoder
from acquisition.frame import Frame
from acquisition.frame_queue import BoundedFrameQueue
from acquisition.mock_camera import MockCamera
from acquisition.writer import WriterThread

CODEC = resolve_encoder("h264_qsv", "libx264")


def _ffprobe_frame_count(path: Path) -> int:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-count_frames", "-show_entries", "stream=nb_read_frames",
            "-of", "json", str(path),
        ],
        capture_output=True,
        timeout=30,
        check=True,
    )
    data = json.loads(result.stdout)
    return int(data["streams"][0]["nb_read_frames"])


@pytest.mark.requires_ffmpeg
def test_mock_capture_produces_playable_h264(tmp_path):
    width = height = 32
    fps = 50

    camera = MockCamera(serial="mock-1", width=width, height=height, fps=fps)
    controller = CaptureController(camera, preroll_duration_s=0.2, fps=fps)
    writer_queue = BoundedFrameQueue(maxsize=200)
    output_path = tmp_path / "t001.mp4"
    writer = WriterThread(
        frame_queue=writer_queue,
        output_path=output_path,
        width=width,
        height=height,
        fps=fps,
        codec=CODEC,
        crf=23,
        pixel_format="yuv420p",
    )

    writer.start()
    controller.start()
    controller.attach_sink(writer_queue)
    time.sleep(1.2)  # ~60 frames at 50 fps
    controller.detach_sink()
    controller.stop()
    writer.stop()
    writer.join(timeout=30)
    writer.raise_if_failed()

    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert writer.frames_written >= 40  # generous floor for scheduling jitter

    frame_count = _ffprobe_frame_count(output_path)
    assert frame_count == writer.frames_written

    rows = writer.timestamp_rows
    assert [r.frame_index for r in rows] == list(range(len(rows)))
    ids = [r.frame_id for r in rows]
    assert ids == list(range(ids[0], ids[0] + len(ids))), "frame IDs not contiguous"


def test_begin_trial_hands_off_preroll_and_live_frames_without_gap_or_duplicate():
    """The pre-roll snapshot and the frames queued after it must be contiguous.
    Snapshotting and attaching as two separate steps let a frame arriving in
    between land in neither (an ID gap) or in both (a duplicate)."""
    fps = 1000  # a 1 ms frame interval makes any handoff window likely to be hit
    camera = MockCamera(serial="mock-handoff", width=8, height=8, fps=fps)
    controller = CaptureController(camera, preroll_duration_s=0.02, fps=fps)
    controller.start()
    try:
        time.sleep(0.05)
        for attempt in range(200):
            sink = BoundedFrameQueue(maxsize=1000)
            preroll = controller.begin_trial(sink)
            time.sleep(0.002)
            controller.detach_sink()
            queued = []
            while sink.qsize():
                queued.append(sink.get(timeout=0).frame_id)
            ids = [f.frame_id for f in preroll] + queued
            assert ids == list(range(ids[0], ids[0] + len(ids))), (
                f"attempt {attempt}: pre-roll ended at {preroll[-1].frame_id}, "
                f"queue began at {queued[:1]}"
            )
    finally:
        controller.stop()


@pytest.mark.requires_ffmpeg
def test_a_recording_cut_off_mid_trial_still_decodes(tmp_path):
    """Simulates a crash mid-trial by truncating the file FFmpeg wrote. A plain
    MP4 is unreadable without the index it writes last; the writer's
    fragmented MP4 must still decode up to the cut."""
    width = height = 64
    frame_queue = BoundedFrameQueue(maxsize=400)
    output = tmp_path / "t001.mp4"
    writer = WriterThread(
        frame_queue=frame_queue, output_path=output, width=width, height=height,
        fps=30, codec="libx264", crf=28, pixel_format="yuv420p", gop=10,
    )
    rng = np.random.default_rng(0)
    for i in range(300):
        frame_queue.put_or_drop(Frame(
            image=rng.integers(0, 256, (height, width), dtype=np.uint8),
            hardware_timestamp_ns=i, frame_id=i,
        ))
    writer.start()
    writer.stop()
    writer.join(timeout=30)
    writer.raise_if_failed()

    data = output.read_bytes()
    crashed = tmp_path / "crashed.mp4"
    crashed.write_bytes(data[: len(data) * 6 // 10])
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-select_streams", "v:0", "-count_frames",
         "-show_entries", "stream=nb_read_frames", "-of", "json", str(crashed)],
        capture_output=True, timeout=30,
    )
    streams = json.loads(result.stdout or b"{}").get("streams", [])
    decoded = int(streams[0].get("nb_read_frames", 0)) if streams else 0
    assert decoded > 100, f"a file cut at 60% decoded only {decoded} of 300 frames"


def test_queue_drops_and_counts_under_backpressure():
    width = height = 8
    fps = 1000  # fast producer, nobody draining the queue

    frame_queue = BoundedFrameQueue(maxsize=3)
    camera = MockCamera(serial="mock-2", width=width, height=height, fps=fps)

    camera.open()
    camera.start_streaming(lambda frame: frame_queue.put_or_drop(frame))
    time.sleep(0.1)  # at 1000fps this offers ~100 frames into a maxsize=3 queue
    camera.stop_streaming()
    camera.close()

    assert frame_queue.dropped_count > 0
    assert frame_queue.qsize() <= frame_queue.maxsize


@pytest.mark.requires_ffmpeg
def test_writer_memory_growth_stays_bounded_over_a_long_run(tmp_path):
    width = height = 32
    fps = 30
    # libx264 (not the resolve_encoder() choice) so this test's throughput
    # reflects Python/queue overhead rather than QSV's per-frame call latency
    # -- the thing under test here is memory flatness, not encoder choice
    # (the primary pipeline test above already exercises the resolved codec).
    codec = "libx264"

    frame_queue = BoundedFrameQueue(maxsize=200)
    writer = WriterThread(
        frame_queue=frame_queue,
        output_path=tmp_path / "long.mp4",
        width=width,
        height=height,
        fps=fps,
        codec=codec,
        crf=28,
        pixel_format="yuv420p",
        poll_timeout_s=0.05,
    )
    writer.start()

    def push_frames(n: int, start_id: int) -> None:
        image = np.zeros((height, width), dtype=np.uint8)
        for i in range(n):
            frame_queue.put_or_drop(
                Frame(image=image, hardware_timestamp_ns=i, frame_id=start_id + i)
            )

    tracemalloc.start()
    push_frames(1000, 0)
    time.sleep(1.0)
    baseline = sum(s.size for s in tracemalloc.take_snapshot().statistics("lineno"))

    push_frames(1000, 1000)
    time.sleep(1.0)
    after = sum(s.size for s in tracemalloc.take_snapshot().statistics("lineno"))
    tracemalloc.stop()

    writer.stop()
    writer.join(timeout=30)
    writer.raise_if_failed()

    growth = after - baseline
    # 1000 more TimestampRow entries is tiny bookkeeping; a real leak (e.g.
    # retaining frame image buffers) would be an order of magnitude larger.
    assert growth < 2_000_000, f"unexpected memory growth: {growth} bytes"
    assert frame_queue.qsize() <= frame_queue.maxsize
    # An unpaced Python loop pushes far faster than any real camera fps, so
    # heavy drop here is expected -- that behavior is what the dedicated
    # backpressure test above proves. This test's only concern is that the
    # writer keeps making progress and memory stays flat under sustained load.
    assert writer.frames_written > 0


def test_resolve_encoder_falls_back_when_preferred_is_unavailable():
    resolved = resolve_encoder("definitely_not_a_real_codec", "libx264")
    assert resolved == "libx264"
