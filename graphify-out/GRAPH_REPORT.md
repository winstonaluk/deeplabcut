# Graph Report - Acquisition  (2026-09-17)

## Corpus Check
- 127 files · ~115,960 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1827 nodes · 3703 edges · 102 communities (84 shown, 17 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 270 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f9327961`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- The acquisition board, as measured
- test_stages_b7_scaffold.py
- session_service.py
- test_kinematics.py
- SpinnakerCamera
- PDCT behavioral acquisition and analysis
- MockCamera
- PixelFormat
- test_session_setup_screen.py
- test_manifest.py
- StereoAcquisition.py
- test_interfaces.py
- Provenance
- NodeMapCallback.py
- test_roundtrip.py
- RecordingSessionController
- TrialPhase
- InterfaceEventHandler
- NodeMapInfo.py
- test_qc_gate.py
- test_orchestration.py
- FileAccess
- ImageEvents.py
- Inference.py
- test_report.py
- LoggingEventHandler
- CaptureController
- pipeline/config.py
- orchestration.py
- BufferHandling.py
- ChunkData.py
- Sequencer.py
- verify_a10.py
- CounterAndTimer.py
- Trigger.py
- Trigger_QuickSpin.py
- TrialStateMachine
- RecordingScreen
- PySpin.Camera
- StereoGPIO.py
- test_recording_session.py
- LookupTable.py
- NodeMapInfo_QuickSpin.py
- Blackfly S BFS-U3-04S2C (serial 22514545)
- Spinnaker SDK Open Source Licenses
- Acquisition.py
- Exposure_QuickSpin.py
- SaveToVideo.py
- Logging levels (Error/Warning/Notice/Info/Debug)
- ImageFormatControl.py
- ImageFormatControl_QuickSpin.py
- AcquireAndDisplay.py
- PySpin.ImagePtr
- PySpin.System
- AcquisitionMultipleCamera.py
- Invariant 2 — Mock Backend Is First-Class
- Stage 1 · qc_gate
- Stage 8 · kinematics
- ImageChannelStatistics.py
- SpinnakerCamera.start_streaming
- PySpin.CameraPtr
- Injected Image: Classification Daisy (grayscale daisy photo)
- GenICam standard
- Enumeration.py
- Enumeration_QuickSpin.py
- Injected Image Detection Aeroplane (test photo)
- test_storage_a8.py
- Encoder Tuning Lever Hierarchy
- Read-Only Nodes = Spinnaker Parameter Lock
- PDCT Analysis Pipeline
- conftest.py
- ssim_and_size
- probe_camera.py
- PySpin.ImageUtility
- SpinUpdate.py
- Node map
- Invariant 6 — Hardware Timestamps Only
- Stage 5 · train
- Shared PySpin System Singleton
- acquisition/__init__.py
- app/__init__.py
- Trial State Machine (IDLE → RECORDING → IDLE)
- gui/__init__.py
- paradigms/__init__.py
- pose/__init__.py
- numpy<2 Upper Bound (acquisition)
- storage/__init__.py
- pipeline/__init__.py
- stages/__init__.py
- FLIR Camera Getting Started (empty file)
- CUDA Toolkit 11.8 (NVIDIA SLA)
- PySpin.ImageList
- pdct-acquisition
- pdct-analysis
- pdct-shared-schema
- SessionService
- test_storage.py
- Frame
- recording_session.py
- test_recording_screen.py
- SKILL.md

## God Nodes (most connected - your core abstractions)
1. `SessionService` - 50 edges
2. `MockCamera` - 47 edges
3. `Frame` - 45 edges
4. `PixelFormat` - 39 edges
5. `RecordingSessionController` - 39 edges
6. `CameraBackend` - 37 edges
7. `SpinnakerCamera` - 37 edges
8. `CaptureController` - 32 edges
9. `BoundedFrameQueue` - 31 edges
10. `WriterThread` - 31 edges

## Surprising Connections (you probably didn't know these)
- `Preflight Checks` --semantically_similar_to--> `Stage 1 · qc_gate`  [INFERRED] [semantically similar]
  acquisition/CLAUDE.md → analysis/CLAUDE.md
- `Invariant 9 — Config Over Literals` --semantically_similar_to--> `PDCT Analysis Pipeline`  [INFERRED] [semantically similar]
  acquisition/CLAUDE.md → analysis/CLAUDE.md
- `Incomplete Frames Counted Separately From Dropped Frames` --shares_data_with--> `Stage 1 · qc_gate`  [INFERRED]
  acquisition/acquisition/SPINNAKER_PLAN.md → analysis/CLAUDE.md
- `Encoder Tuning Lever Hierarchy` --semantically_similar_to--> `Single-Camera Kinematics Are Provisional`  [INFERRED] [semantically similar]
  acquisition/CLAUDE.md → analysis/CLAUDE.md
- `Invariant 6 — Hardware Timestamps Only` --semantically_similar_to--> `Invariant 12 — Analysis fps Decoupled from Acquisition fps`  [INFERRED] [semantically similar]
  acquisition/CLAUDE.md → analysis/CLAUDE.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Analysis Pipeline Stage Chain (0 → 9)** — analysis_claude_build_manifest, analysis_claude_qc_gate, analysis_claude_calibration, analysis_claude_extract_frames, analysis_claude_labeling, analysis_claude_train, analysis_claude_evaluate, analysis_claude_infer, analysis_claude_kinematics, analysis_claude_report [EXTRACTED 1.00]
- **CameraBackend Interface and Its Implementations** — acquisition_claude_camerabackend, acquisition_claude_mockcamera, acquisition_claude_spinnakercamera, acquisition_claude_invariant_2_mock_first_class [EXTRACTED 1.00]
- **Two paths to camera parameters: QuickSpin vs GenAPI node map** — docs_spinnaker_python_programmer_guide_quickspin_api, docs_spinnaker_python_programmer_guide_genapi, docs_spinnaker_python_programmer_guide_nodemap, docs_spinnaker_python_programmer_guide_camera_xml, docs_pyspindoc_quickspin_classes [EXTRACTED 1.00]
- **SpinnakerCamera Lifecycle Methods** — acquisition_acquisition_spinnaker_plan_open, acquisition_acquisition_spinnaker_plan_load_user_set, acquisition_acquisition_spinnaker_plan_verify_settings, acquisition_acquisition_spinnaker_plan_start_streaming, acquisition_acquisition_spinnaker_plan_stop_streaming, acquisition_acquisition_spinnaker_plan_close, acquisition_acquisition_spinnaker_plan_system_singleton [EXTRACTED 1.00]
- **Spinnaker event handler family** — docs_pyspindoc_eventhandler, docs_pyspindoc_systemeventhandler, docs_pyspindoc_interfaceeventhandler, docs_pyspindoc_deviceeventhandler, docs_pyspindoc_imageeventhandler, docs_pyspindoc_loggingeventhandler [EXTRACTED 1.00]
- **Spinnaker image acquisition pipeline** — docs_pyspindoc_system, docs_pyspindoc_cameralist, docs_pyspindoc_camera, docs_pyspindoc_imageptr, docs_pyspindoc_spinvideo, docs_spinnaker_python_programmer_guide_grabbing_images [INFERRED 0.85]

## Communities (102 total, 17 thin omitted)

### Community 0 - "The acquisition board, as measured"
Cohesion: 0.18
Nodes (10): Camera streaming, Encoding, GPIO, Identity, Inference and closed-loop latency, Still unmeasured, The acquisition board, as measured, The dependency stack (highest-risk item in the plan) (+2 more)

### Community 1 - "test_stages_b7_scaffold.py"
Cohesion: 0.05
Nodes (75): EvaluationReport, FrameManifestRow, PoseIndexRow, Stage-contract dataclasses: one row per record, long/tidy and view-tagged…, Stage 7 (infer, B7 scaffold) output: pose_index.parquet., Stage 3 (extract_frames, B7 scaffold) output: frames_manifest.csv., Stage 5 (train, B7 scaffold) output: training_log.json., Stage 6 (evaluate, B7 scaffold) output: evaluation_report.json. (+67 more)

### Community 2 - "session_service.py"
Cohesion: 0.07
Nodes (40): build_camera(), _mock(), Maps a camera's config ``type`` to a concrete :class:`CameraBackend`. One dict,…, Constructs the backend named by ``camera.type``. Geometry, pixel format and…, _spinnaker(), CameraConfig, CaptureConfig, ConfigError (+32 more)

### Community 3 - "test_kinematics.py"
Cohesion: 0.07
Nodes (63): KinematicsConfig, CalibrationRecord, Stage 2 (calibration) output data contract. The calibration stage itself --…, apply_likelihood_filter(), compute_pole_frame(), compute_trial_kinematics(), compute_velocity(), detect_descent() (+55 more)

### Community 4 - "SpinnakerCamera"
Cohesion: 0.05
Nodes (47): CameraError, RuntimeError, A camera failed to open, load its UserSet, or stream., _acquire_system(), _find_enum_entry(), _make_frame_event_handler(), _node_value_str(), _normalize_enum_name() (+39 more)

### Community 5 - "PDCT behavioral acquisition and analysis"
Cohesion: 0.22
Nodes (8): Acquisition setup, Analysis setup, Knowledge graph, PDCT behavioral acquisition and analysis, Run it, Tests, The shared schema, Why two environments

### Community 6 - "MockCamera"
Cohesion: 0.07
Nodes (31): NodeCheck, One camera setting read back and compared against its expected value. Values…, Reads back each named camera node and compares it to ``expected``. Read-only by…, MockCamera, FrameCallback, Every check passes: a synthetic camera has no real nodes to contradict the…, Path, Runs every check and returns all outcomes. Deliberately does not short-circuit… (+23 more)

### Community 7 - "PixelFormat"
Cohesion: 0.06
Nodes (24): CameraBackend, ABC, FrameCallback, Camera abstraction. SpinnakerCamera and MockCamera both implement this. Every…, Begins delivering frames to ``on_frame`` from the backend's own thread. Must…, Stops frame delivery. Idempotent if not currently streaming., The camera's serial number (or a synthetic one for MockCamera)., ``(width, height)`` actually being delivered, read from the camera. Not the… (+16 more)

### Community 8 - "test_session_setup_screen.py"
Cohesion: 0.11
Nodes (23): _camera_checks(), PreflightCheck, PreflightResult, Preflight checks: camera detected, UserSet loaded, camera settings verified…, One named check and its outcome. Passing checks are retained, not just…, Why the most recent load_user_set() returned False, if it did. Lets preflight…, MetadataConfig, QWidget (+15 more)

### Community 9 - "test_manifest.py"
Cohesion: 0.16
Nodes (27): build_manifest(), compute_manifest_input_hashes(), dataframe_to_manifest_rows(), _find_trial_file(), DataFrame, Path, Scans every session directory under archive_root. A directory counts as a…, One hash per session's session_metadata.json/trials.csv -- if any session's… (+19 more)

### Community 10 - "StereoAcquisition.py"
Cohesion: 0.09
Nodes (33): acquire_images(), compute_3d_point_cloud_and_save(), configure_chunk_data(), configure_stereo_params(), disable_chunk_data(), display_chunk_data_from_image(), enable_camera_stream(), enable_node() (+25 more)

### Community 11 - "test_interfaces.py"
Cohesion: 0.06
Nodes (35): KeypressStopCondition, ABC, Pluggable predicate consulted by ``TrialStateMachine.tick()`` to decide whether…, The PDCT default: stops only when externally signalled. The Qt spacebar handler…, TrialStopCondition, Paradigm, ABC, Paradigm ABC: what varies between PDCT and any future task. A paradigm supplies… (+27 more)

### Community 12 - "Provenance"
Cohesion: 0.14
Nodes (23): current_code_commit(), hash_config(), hash_file(), make_provenance(), Provenance, provenance_path_for(), Any, datetime (+15 more)

### Community 13 - "NodeMapCallback.py"
Cohesion: 0.09
Nodes (26): acquire_images(), change_height_and_gain(), configure_callbacks(), configure_event_callbacks(), EventNodeCallback, GainNodeCallback, HeightNodeCallback, main() (+18 more)

### Community 14 - "test_roundtrip.py"
Cohesion: 0.05
Nodes (55): QKeyEvent, QWidget, Review screen (screen 3 of 3, skippable): trial table, flag editing, note…, ReviewScreen, Path, Loads a completed session's trials.csv for review: flag editing, note entry,…, ReviewSessionController, _key_event() (+47 more)

### Community 15 - "RecordingSessionController"
Cohesion: 0.12
Nodes (9): CameraRig, datetime, Path, Currently recording trial if active, else most recently completed…, Periodic call (GUI timer): advances max-duration / stop-condition auto-stop and…, Reason-code hotkey handler. Toggles on the target trial and re-persists…, Ctrl+Delete: removes the last completed trial's video, sidecar, and record.…, One camera's live capture pipeline for the session. (+1 more)

### Community 16 - "TrialPhase"
Cohesion: 0.14
Nodes (20): Enum, What ``request_toggle()`` actually did, so the GUI can react (e.g. show the…, TrialPhase, TrialToggleAction, FakeClock, _machine(), ManualStopCondition, Checkpoint A3: min-duration swallow, max-duration auto-stop, suspicious-short… (+12 more)

### Community 17 - "InterfaceEventHandler"
Cohesion: 0.10
Nodes (14): check_gev_enabled(), InterfaceEventHandler, main(), This class defines the properties and methods of the system event handler that…, Constructor. This sets the system instance. :param system: Instance of the…, This method defines the interface arrival event callback on the system. It…, This method defines the interface removal event callback on the system. It…, This function checks if GEV enumeration is enabled on the system. :param… (+6 more)

### Community 18 - "NodeMapInfo.py"
Cohesion: 0.12
Nodes (26): main(), print_boolean_node(), print_category_node_and_all_features(), print_command_node(), print_enumeration_node_and_current_entry(), print_float_node(), print_integer_node(), print_string_node() (+18 more)

### Community 19 - "test_qc_gate.py"
Cohesion: 0.16
Nodes (27): ManifestRow, QCRow, Stage 0 (build_manifest) output: manifest.parquet, one row per trial x view., Stage 1 (qc_gate) output: manifest_qc.parquet = ManifestRow +…, manifest_rows_to_dataframe(), frozenset fields become sorted lists -- parquet has no set type, and a…, evaluate_trial(), DataFrame (+19 more)

### Community 20 - "test_orchestration.py"
Cohesion: 0.18
Nodes (25): Runs stages from_stage..to_stage inclusive, in registry order, skipping any…, run_pipeline(), _config(), _fake_chain(), parametrize, Path, Checkpoint B6: per-stage commands, run --from --to, status, --dry-run.…, kinematics isn't wired (see QUESTIONS.md), so this places fake… (+17 more)

### Community 21 - "FileAccess"
Cohesion: 0.12
Nodes (14): FileAccess, ImageAcquisitionUtil, main(), This function executes delete operation on the camera. :param cam: Camera used…, This function opens the camera file for writing. :param cam: Camera used to…, This function executes write command on the camera. :param cam: Camera used to…, This function closes the file. :param cam: Camera used to perform file…, This function first acquires a reference image from the camera, then it writes… (+6 more)

### Community 22 - "ImageEvents.py"
Cohesion: 0.10
Nodes (21): acquire_images(), configure_image_events(), ImageEventHandler, main(), print_device_info(), Getter for image count. :return: Number of images saved. :rtype: int, Getter for maximum images. :return: Total number of images to save. :rtype: int, This function configures the example to execute image events by preparing and… (+13 more)

### Community 23 - "Inference.py"
Cohesion: 0.14
Nodes (25): acquire_images(), camera_close_file(), camera_delete_file(), camera_open_file(), camera_write_to_file(), configure_chunk_data(), configure_inference(), configure_test_pattern() (+17 more)

### Community 24 - "test_report.py"
Cohesion: 0.17
Nodes (28): KinematicsLongRow, Stage 8 (kinematics, B4) output: kinematics_long.parquet -- one row per frame x…, Stage 8 (kinematics, B4) output: trial_summary.parquet -- one row per trial., TrialSummaryRow, aggregate_by_keypoint(), aggregate_overall(), aggregate_velocity_by_height(), _descent_summary_stats() (+20 more)

### Community 25 - "LoggingEventHandler"
Cohesion: 0.29
Nodes (5): LoggingEventHandler, main(), Although logging events are just as flexible and extensible as other events,…, This function displays readily available logging information. :param…, Example entry point; notice the volume of data that the logging event handler…

### Community 26 - "CaptureController"
Cohesion: 0.10
Nodes (7): CaptureController, Wires one CameraBackend's frame callback to the pre-roll buffer, a latest-frame…, What the camera is actually delivering -- the writer sizes its FFmpeg pipe from…, For preview only (invariant 5) -- reads the latest frame rather than consuming…, PreRollBuffer, Rolling in-RAM buffer of the most recent N seconds. Runs whenever streaming,…, Frames in chronological order. Does not clear the buffer -- preroll keeps…

### Community 27 - "pipeline/config.py"
Cohesion: 0.16
Nodes (18): CalibrationEpoch, ConfigError, KeypointsConfig, load_config(), PathsConfig, Path, ValueError, QCConfig (+10 more)

### Community 28 - "orchestration.py"
Cohesion: 0.24
Nodes (17): AnalysisConfig, config_hash_for(), derived_path(), _manifest_input_hashes(), Path, _qc_input_hashes(), Per-stage commands, run --from --to (skipping cached), status (what's stale and…, One hash for the whole config, deliberately coarse: any config change… (+9 more)

### Community 29 - "BufferHandling.py"
Cohesion: 0.15
Nodes (18): acquire_images(), configure_trigger(), get_expected_image_count(), grab_next_image_by_trigger(), main(), print_device_info(), This function retrieves a single image using the trigger. In this example, only…, This function returns the camera to a normal state by turning off trigger mode.… (+10 more)

### Community 30 - "ChunkData.py"
Cohesion: 0.15
Nodes (18): acquire_images(), ChunkDataTypes, configure_chunk_data(), disable_chunk_data(), display_chunk_data_from_image(), display_chunk_data_from_nodemap(), main(), print_device_info() (+10 more)

### Community 31 - "Sequencer.py"
Cohesion: 0.17
Nodes (18): acquire_images(), configure_sequencer_part_one(), configure_sequencer_part_two(), main(), print_device_info(), print_retrieve_node_failure(), This function sets a single state. It sets the sequence number, applies custom…, Now that the states have all been set, this function readies the camera to use… (+10 more)

### Community 32 - "verify_a10.py"
Cohesion: 0.13
Nodes (14): probe_encoder(), FFmpeg encoder capability probing and fallback selection. h264_qsv (Intel Quick…, Runs a throwaway 1-frame encode. Returns True iff it succeeds., Returns ``preferred`` if it actually works here, else ``fallback``. Never…, resolve_encoder(), Bounded, drop-on-full frame queue between capture and the writer thread.…, Consumes frames from a bounded queue and pipes them to FFmpeg as raw video.…, test_resolve_encoder_falls_back_when_preferred_is_unavailable() (+6 more)

### Community 33 - "CounterAndTimer.py"
Cohesion: 0.16
Nodes (17): acquire_images(), configure_digital_io(), configure_exposure_and_trigger(), main(), print_device_info(), This function configures the GPIO to output the PWM signal. :param nodemap:…, This function configures the camera to set a manual exposure value and enables…, This function acquires and saves 10 images from a device; please see… (+9 more)

### Community 34 - "Trigger.py"
Cohesion: 0.15
Nodes (17): acquire_images(), configure_trigger(), grab_next_image_by_trigger(), main(), print_device_info(), This function acquires an image by executing the trigger node. :param cam:…, # TODO: Blackfly and Flea3 GEV cameras need 2 second delay after software…, This function acquires and saves 10 images from a device. Please see… (+9 more)

### Community 35 - "Trigger_QuickSpin.py"
Cohesion: 0.15
Nodes (17): acquire_images(), configure_trigger(), grab_next_image_by_trigger(), main(), print_device_info(), This function acquires an image by executing the trigger node. :param cam:…, # TODO: Blackfly and Flea3 GEV cameras need 2 second delay after software…, This function acquires and saves 10 images from a device. Please see… (+9 more)

### Community 36 - "TrialStateMachine"
Cohesion: 0.14
Nodes (10): Seconds since the current trial started; 0.0 while IDLE., Non-destructive peek at the most recently completed trial's outcome -- unlike…, Spacebar handler entry point. Starts a trial from IDLE, stops one from…, Periodic check (e.g. a Qt timer) for max-duration auto-stop and…, Ctrl+Delete handler: discards the last completed trial after confirmation is…, Owns trial phase and timing guards for one paradigm's trials. Not itself a Qt…, TrialStateMachine, TrialToggleResult (+2 more)

### Community 37 - "RecordingScreen"
Cohesion: 0.30
Nodes (5): frame_to_pixmap(), QKeyEvent, QWidget, RecordingScreen, QPixmap

### Community 38 - "PySpin.Camera"
Cohesion: 0.13
Nodes (16): PySpin.Camera, PySpin.CameraBase, PySpin.ChannelStatistics, PySpin.ChunkData, PySpin.Image, QuickSpin classes (Chapter 5), PySpin.TransportLayerDevice, PySpin.TransportLayerInterface (+8 more)

### Community 39 - "StereoGPIO.py"
Cohesion: 0.18
Nodes (15): acquire_images(), configure_gpio(), main(), print_device_info(), This function sets the trigger mode to on/off. :param nodemap: Transport layer…, This function acquires and saves multiple image sets from a device. :param cam:…, This function prints the device information of the camera from the transport…, This function acts as the body of the example; please see NodeMapInfo example… (+7 more)

### Community 41 - "test_recording_session.py"
Cohesion: 0.25
Nodes (21): hardware_fps(), Frames per second measured on the camera's own clock. ``(n - 1) / span`` over…, _make_controller(), _make_rig(), requires_ffmpeg, Checkpoint A6 core: RecordingSessionController orchestrates capture, writing,…, Pre-roll frames are in the file but precede the trial's start, so counting them…, _teardown() (+13 more)

### Community 42 - "LookupTable.py"
Cohesion: 0.19
Nodes (14): acquire_images(), configure_lookup_tables(), main(), print_device_info(), print_retrieve_node_failure(), This function resets the camera by disabling lookup tables. :param nodemap:…, # This function prints the device information of the camera from the transport…, This function acquires and saves 10 images from a device; please see… (+6 more)

### Community 43 - "NodeMapInfo_QuickSpin.py"
Cohesion: 0.21
Nodes (14): main(), print_genicam_device_info(), print_node_info(), print_transport_layer_device_info(), print_transport_layer_interface_info(), print_transport_layer_stream_info(), Prints stream information from transport layer. *** NOTES *** In QuickSpin,…, Prints stream information from the transport layer. *** NOTES *** In QuickSpin,… (+6 more)

### Community 44 - "Blackfly S BFS-U3-04S2C (serial 22514545)"
Cohesion: 0.22
Nodes (9): Blackfly S BFS-U3-04S2C (serial 22514545), 60-Second Pipeline Measurement Under Load, SpinnakerCamera.open(), Checkpoint A10 — SpinnakerCamera Implementation, Checkpoint A9.5 — Camera Backend Schema, Storage Management and Transfer Staging, tomli Backport for Python 3.10, A9.5 · chunk-data enablement vs. invariant 7 (+1 more)

### Community 45 - "Spinnaker SDK Open Source Licenses"
Cohesion: 0.14
Nodes (14): Spinnaker SDK Open Source Licenses, FreeImage (FreeImage Public License v1.0), NumPy (BSD 3-clause), Spinnaker Component: PySpin, Qt 5.7 (LGPL v3), RapidXml (MIT, documentation component), PySpin API Reference (Release 4.3), PySpin.ImageProcessor (+6 more)

### Community 46 - "Acquisition.py"
Cohesion: 0.19
Nodes (13): acquire_images(), main(), print_device_info(), This function acquires and saves 10 images from a device. :param cam: Camera to…, This function prints the device information of the camera from the transport…, This function acts as the body of the example; please see NodeMapInfo example…, Example entry point; please see Enumeration example for more in-depth comments…, # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being… (+5 more)

### Community 47 - "Exposure_QuickSpin.py"
Cohesion: 0.20
Nodes (13): acquire_images(), configure_exposure(), main(), print_device_info(), This function returns the camera to a normal state by re-enabling automatic…, This function prints the device information of the camera from the transport…, This function acquires and saves 10 images from a device; please see…, This function acts as the body of the example; please see NodeMapInfo_QuickSpin… (+5 more)

### Community 48 - "SaveToVideo.py"
Cohesion: 0.19
Nodes (13): acquire_images(), main(), print_device_info(), This function prints the device information of the camera from the transport…, This function acquires 30 images from a device, stores them in a list, and…, This function acts as the body of the example; please see NodeMapInfo example…, Example entry point; please see Enumeration example for more in-depth comments…, Enum' to select video type to be created and saved (+5 more)

### Community 49 - "Logging levels (Error/Warning/Notice/Info/Debug)"
Cohesion: 0.17
Nodes (12): log4cpp / log4net logging libraries, Spinnaker Component: SpinView, PySpin.LoggingEventDataPtr, PySpin.LoggingEventHandler, PySpin.SpinnakerException, Chunk Data, Error Handling (try/except SpinnakerException), Spinnaker SDK code examples catalog (+4 more)

### Community 50 - "ImageFormatControl.py"
Cohesion: 0.23
Nodes (11): acquire_images(), configure_custom_image_settings(), main(), print_device_info(), This function prints the device information of the camera from the transport…, This function acquires and saves 10 images from a device. :param cam: Camera to…, This function acts as the body of the example; please see NodeMapInfo example…, Example entry point; please see Enumeration example for more in-depth comments… (+3 more)

### Community 51 - "ImageFormatControl_QuickSpin.py"
Cohesion: 0.23
Nodes (11): acquire_images(), configure_custom_image_settings(), main(), print_device_info(), This function prints the device information of the camera from the transport…, This function acquires and saves 10 images from a device; please see…, This function acts as the body of the example; please see NodeMapInfo_QuickSpin…, Example entry point; please see Enumeration_QuickSpin example for more in-depth… (+3 more)

### Community 52 - "AcquireAndDisplay.py"
Cohesion: 0.24
Nodes (10): acquire_and_display_images(), handle_close(), main(), This function acts as the body of the example; please see NodeMapInfo example…, # NOTE: keyboard and matplotlib must be installed on Python interpreter prior…, Example entry point; notice the volume of data that the logging event handler…, # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being…, This function will close the GUI when close event happens. :param evt: Event… (+2 more)

### Community 54 - "PySpin.ImagePtr"
Cohesion: 0.22
Nodes (10): ffmpeg (LGPL v2.1 or later), Intel Performance Primitives (IPP), Spinnaker Component: SpinVideo, PySpin.AVIOption / H264 MP4 options, PySpin.ImagePtr, Reference-tracked smart pointer lifetime, PySpin.SpinVideo, Grabbing Images (GetNextImage) (+2 more)

### Community 55 - "PySpin.System"
Cohesion: 0.22
Nodes (10): PySpin.CameraList, PySpin.IInterface, PySpin.InterfaceList, PySpin.InterfacePtr, PySpin.System, System Singleton lifecycle, PySpin.SystemEventHandler, PySpin.SystemPtr (+2 more)

### Community 56 - "AcquisitionMultipleCamera.py"
Cohesion: 0.27
Nodes (9): acquire_images(), main(), print_device_info(), This function prints the device information of the camera from the transport…, This function acts as the body of the example; please see NodeMapInfo example…, # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being…, Example entry point; please see Enumeration example for more in-depth comments…, This function acquires and saves 10 images from each device. :param cam_list:… (+1 more)

### Community 57 - "Invariant 2 — Mock Backend Is First-Class"
Cohesion: 0.25
Nodes (8): PySpin Exception Translation Convention, CameraBackend Abstraction, Invariant 2 — Mock Backend Is First-Class, MockCamera Backend, SpinnakerCamera Backend, PySpin Is Vendor-Distributed, Not on PyPI, FLIR Spinnaker SDK License Agreement, spinnaker-python Wheel Name

### Community 58 - "Stage 1 · qc_gate"
Cohesion: 0.17
Nodes (13): Acquisition-Side Cross-Repo Contract, Session Directory and Filename Convention, Invariant 8 — Trial Stop Is a Pluggable Predicate, Reason-Code Hotkey Flagging, Stage 0 · build_manifest, Invariant 3 — QC Marks, Never Deletes, Stage 1 · qc_gate, Stage 9 · report (+5 more)

### Community 60 - "Stage 8 · kinematics"
Cohesion: 0.24
Nodes (10): RTX 5070 Ti / Blackwell sm_120 cu128 Requirement, Stage 2 · calibration, Archive / Cache / Derived Data Tiering, Stage 7 · infer, Invariant 2 — Undistort Coordinates, Never Video, Stage 8 · kinematics, opencv-python-headless for Coordinate Undistortion Only, DeepLabCut and torch Deliberately Excluded (+2 more)

### Community 61 - "ImageChannelStatistics.py"
Cohesion: 0.28
Nodes (8): acquire_and_display_images(), main(), This function acts as the body of the example; please see NodeMapInfo example…, Example entry point; notice the volume of data that the logging event handler…, # NOTE: matplotlib must be installed on Python interpreter prior to running…, # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being…, This function acquires and displays the channel statistics of N images from a…, run_single_camera()

### Community 62 - "SpinnakerCamera.start_streaming"
Cohesion: 0.33
Nodes (6): 720 × 540 Sensor Correction (not 1280 × 720), Copy GetNDArray() Before the Frame Escapes, Incomplete Frames Counted Separately From Dropped Frames, SpinnakerCamera.start_streaming(), Invariant 3 — Capture Never Blocks, Pre-Roll Ring Buffer (2 s)

### Community 64 - "PySpin.CameraPtr"
Cohesion: 0.25
Nodes (8): PySpin.CameraPtr, PySpin.DeviceArrivalEventHandler, PySpin.DeviceEventHandler, PySpin.DeviceRemovalEventHandler, PySpin.EventHandler, PySpin.ImageEventHandler, PySpin.InterfaceEventHandler, Event Handling (interface and device events)

### Community 65 - "Injected Image: Classification Daisy (grayscale daisy photo)"
Cohesion: 0.39
Nodes (8): Injected Image: Classification Daisy (grayscale daisy photo), Daisy Class Label (expected classifier output), Deterministic Test Input Without a Live Scene, High-Contrast Centered Subject on Smooth Gradient Background, Spinnaker Image Injection (file substituted for live sensor frames), On-Camera Inference: Image Classification, Monochrome Single-Channel Frame Content, PySpin Example Scripts Bundle

### Community 66 - "GenICam standard"
Cohesion: 0.33
Nodes (7): GenICam by EMVA (licensed component), Spinnaker Component: GenTL, Xerces-C++ and libexpat XML parsers, PySpin.CBasePtr (GenApi pointer), Spinnaker SDK Python Programmer's Guide, Camera XML description file, GenICam standard

### Community 67 - "Enumeration.py"
Cohesion: 0.33
Nodes (6): main(), query_interface(), # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being…, Example entry point. :return: True if successful, False otherwise. :rtype: bool, # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being…, Queries an interface for its cameras and prints out device information. :param…

### Community 68 - "Enumeration_QuickSpin.py"
Cohesion: 0.33
Nodes (6): main(), query_interface(), # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being…, Example entry point. :return: True if successful, False otherwise. :rtype: bool, # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being…, Queries an interface for its cameras and prints out device information. :param…

### Community 69 - "Injected Image Detection Aeroplane (test photo)"
Cohesion: 0.48
Nodes (7): Injected Image Detection Aeroplane (test photo), Expected class label 'aeroplane' (ground truth for the detection demo), Spinnaker image injection (file fed into the camera stream in place of the sensor), On-camera inference / detection example (Firefly DL neural-network classification), Grayscale / Mono8-compatible imagery (no color channels), PySpin / Spinnaker SDK example asset bundle (docs/PySpinExamples), Photographic subject: twin-engine airliner on approach through storm clouds (monochrome)

### Community 70 - "test_storage_a8.py"
Cohesion: 0.11
Nodes (34): check_disk_status(), DiskStatus, estimate_remaining_minutes(), existing_ancestor(), free_space_gb(), measure_bitrate_mb_per_min(), Path, Free-space indicator and remaining-recording-time estimate. "GB free is not… (+26 more)

### Community 71 - "Encoder Tuning Lever Hierarchy"
Cohesion: 0.33
Nodes (6): Auto-Exposure / Auto-Gain Covariance Problem, Encoder Tuning Lever Hierarchy, Single-Camera Kinematics Are Provisional, Future · triangulate (Anipose 3D), FFmpeg LGPL v2.1 Compliance Notice, A9.5 · encoder quality scales were shared (RESOLVED)

### Community 72 - "Read-Only Nodes = Spinnaker Parameter Lock"
Cohesion: 0.20
Nodes (9): Read-Only Nodes = Spinnaker Parameter Lock, Transport-Layer Stream Buffer Settings, UserSet1 Has Never Been Configured, SpinnakerCamera.verify_settings(), Invariant 7 — No Camera Configuration UI, Preflight Checks, UserSet1 Camera Settings Profile, A9.5 · UserSet verification list resolved by measurement (+1 more)

### Community 73 - "PDCT Analysis Pipeline"
Cohesion: 0.22
Nodes (9): Behavioral Video Acquisition GUI, Checkpoint A11 — Application Wiring (Composition Root), Invariant 9 — Config Over Literals, PDCT (Pole Descent Cognitive Test), Invariant 5 — Every Artifact Carries Provenance, PDCT Analysis Pipeline, y(t) — Trustworthy Scaled Vertical Position Series, Monorepo Layout (shared/schema + acquisition + analysis) (+1 more)

### Community 74 - "conftest.py"
Cohesion: 0.33
Nodes (5): fixture, pytest_collection_modifyitems(), qapp(), Forces offscreen Qt rendering so GUI tests run with zero display attached --…, Skips FFmpeg-dependent tests when FFmpeg isn't installed. FFmpeg is an external…

### Community 75 - "ssim_and_size"
Cohesion: 0.40
Nodes (5): main(), Path, Sweep encoder settings over real footage and report size against quality.…, Encodes once and returns (ssim, bytes, encode_seconds)., ssim_and_size()

### Community 76 - "probe_camera.py"
Cohesion: 0.33
Nodes (3): load_user_set(), Probe of the attached FLIR camera. python tools/probe_camera.py # read-only…, Executes UserSetLoad for `name`. Returns None on success, else why not.

### Community 77 - "PySpin.ImageUtility"
Cohesion: 0.33
Nodes (6): PySpin.ImageUtility, PySpin.ImageUtilityCCM, PySpin.ImageUtilityHeatmap, PySpin.ImageUtilityPolarization, PySpin.ImageUtilityStereo, PySpin.PointCloud

### Community 78 - "SpinUpdate.py"
Cohesion: 0.47
Nodes (5): main(), message_callback(), progress_callback(), Example progress callback function. NOTE: This function must take exactly 4…, Example message callback function. NOTE: This function must take exactly 1…

### Community 79 - "Node map"
Cohesion: 0.33
Nodes (6): BlackLevel feature, ExposureTime feature, Gain feature, Gamma feature, Node map, White Balance / BalanceRatio

### Community 80 - "Invariant 6 — Hardware Timestamps Only"
Cohesion: 0.40
Nodes (5): Chunk Data Off As Shipped, Spinnaker Chunk Data (FrameID + Timestamp), Invariant 6 — Hardware Timestamps Only, Invariant 12 — Analysis fps Decoupled from Acquisition fps, B3 · qc.nominal_fps as its own config key

### Community 81 - "Stage 5 · train"
Cohesion: 0.40
Nodes (5): Stage 6 · evaluate, Stage 3 · extract_frames, Stage 4 · labeling (manual), Open Experimental-Design Decisions, Stage 5 · train

### Community 82 - "Shared PySpin System Singleton"
Cohesion: 0.67
Nodes (3): Shared PySpin System Singleton, Invariant 1 — N-Camera by Construction, Manual Release of CameraPtr / CameraList / SystemPtr

### Community 100 - "SessionService"
Cohesion: 0.05
Nodes (48): AppConfig, main(), parse_args(), Path, CLI entry point. python -m app --mock --headless # full session, synthetic…, run_headless(), _with_session_root(), CameraState (+40 more)

### Community 101 - "test_storage.py"
Cohesion: 0.15
Nodes (25): build_session_metadata(), datetime, Assembles SessionMetadata at session lock (A5) from config + runtime info., create_session_directory(), datetime, Path, Session directory and trial filename generation. See acquisition/CLAUDE.md…, Refusing to overwrite an existing session directory (never allowed). (+17 more)

### Community 102 - "Frame"
Cohesion: 0.07
Nodes (30): Attaches ``sink`` and returns the pre-roll to prepend, atomically. The returned…, Begins forwarding frames to ``sink`` with no pre-roll handoff. A trial with a…, Frame, BoundedFrameQueue, Enqueues ``frame``. Never blocks. Returns False and increments the drop counter…, Blocks up to ``timeout`` seconds. Raises queue.Empty on timeout., One captured image plus its camera-supplied chunk data.…, Path (+22 more)

### Community 105 - "recording_session.py"
Cohesion: 0.24
Nodes (9): Orchestrates capture, writing, and trial state for one locked session. The rig…, IDLE -> RECORDING -> IDLE trial state machine. Guards: min-duration swallow,…, A completed trial's timing and auto-applied flags. Experimenter-assigned flags…, TrialOutcome, Recording screen (screen 2 of 3): preview tiles, large-font readouts, spacebar…, build_trial_record(), datetime, Bridges TrialStateMachine's TrialOutcome (monotonic timing, no wall-clock… (+1 more)

### Community 110 - "test_recording_screen.py"
Cohesion: 0.40
Nodes (9): _key_event(), _make_screen(), requires_ffmpeg, Checkpoint A6 GUI shell: spacebar control, reason-code hotkeys, visual flag…, test_ctrl_delete_discards_last_trial(), test_dropped_frames_readout_updates_via_timer_tick(), test_preview_tile_created_per_camera_rig(), test_reason_code_hotkey_toggles_flag_and_chip_style() (+1 more)

## Ambiguous Edges - Review These
- `Qt 5.7 (LGPL v3)` → `C# Graphical User Interface API`  [AMBIGUOUS]
  docs/licenses/Spinnaker-Open-Source-Licenses.pdf · relation: semantically_similar_to
- `Spinnaker image injection (file fed into the camera stream in place of the sensor)` → `Grayscale / Mono8-compatible imagery (no color channels)`  [AMBIGUOUS]
  docs/PySpinExamples/Injected_Image_Detection_Aeroplane.jpg · relation: rationale_for
- `On-camera inference / detection example (Firefly DL neural-network classification)` → `Photographic subject: twin-engine airliner on approach through storm clouds (monochrome)`  [AMBIGUOUS]
  docs/PySpinExamples/Injected_Image_Detection_Aeroplane.jpg · relation: rationale_for
- `FLIR Camera Getting Started (empty file)` → `PySpin vs C++ API Differences`  [AMBIGUOUS]
  docs/FLIR Camera Getting Started.html · relation: conceptually_related_to

## Knowledge Gaps
- **77 isolated node(s):** `pdct-acquisition`, `pdct-analysis`, `ChunkDataTypes`, `TriggerType`, `TriggerType` (+72 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 677 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Qt 5.7 (LGPL v3)` and `C# Graphical User Interface API`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `Spinnaker image injection (file fed into the camera stream in place of the sensor)` and `Grayscale / Mono8-compatible imagery (no color channels)`?**
  _Edge tagged AMBIGUOUS (relation: rationale_for) - confidence is low._
- **What is the exact relationship between `On-camera inference / detection example (Firefly DL neural-network classification)` and `Photographic subject: twin-engine airliner on approach through storm clouds (monochrome)`?**
  _Edge tagged AMBIGUOUS (relation: rationale_for) - confidence is low._
- **What is the exact relationship between `FLIR Camera Getting Started (empty file)` and `PySpin vs C++ API Differences`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `SessionService` connect `SessionService` to `session_service.py`, `TrialStateMachine`, `Frame`, `PixelFormat`, `test_session_setup_screen.py`, `test_interfaces.py`, `test_roundtrip.py`, `RecordingSessionController`, `TrialPhase`, `CaptureController`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `Frame` connect `Frame` to `verify_a10.py`, `session_service.py`, `SessionService`, `RecordingScreen`, `MockCamera`, `PixelFormat`, `recording_session.py`, `test_interfaces.py`, `CaptureController`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `CameraBackend` connect `PixelFormat` to `session_service.py`, `SpinnakerCamera`, `SessionService`, `MockCamera`, `test_session_setup_screen.py`, `test_interfaces.py`, `CaptureController`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._