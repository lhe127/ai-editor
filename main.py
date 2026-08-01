"""
Application Entry Point for BTIS3053 AI-Assisted Multi-Camera Video Editing Pipeline.
Supports PySide6 GUI mode and automated CLI mode.
"""
import sys
import argparse
import logging
from pathlib import Path

# Set up logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

import config
from synchronization.audio_sync import AudioSynchronizer
from synchronization.timeline import MasterTimeline
from selection.motion import MotionAnalyzer
from selection.camera_selector import CameraSelector
from edl.edl_manager import EDLManager
from renderer.moviepy_renderer import MoviePyRenderer

def run_cli_pipeline(draft_mode: bool = False):
    """Execute complete end-to-end video pipeline in headless CLI mode."""
    mode_str = "FAST DRAFT MODE (480p @ 15fps)" if draft_mode else "MASTER MODE (720p @ 30fps)"
    logger.info(f"=== Running BTIS3053 Video Editing Pipeline (CLI Mode) [{mode_str}] ===")

    # 1. Detect Camera Files
    camera_files = {}
    for cam_id in config.CAMERA_KEYS:
        for ext in [".mp4", ".mts", ".m2ts", ".mov"]:
            target = config.VIDEOS_DIR / f"{cam_id.lower()}{ext}"
            if target.exists():
                camera_files[cam_id] = str(target)
                break

    if not camera_files:
        logger.error(f"No test camera videos found in {config.VIDEOS_DIR}. Please run 'python scripts/generate_test_videos.py' first.")
        sys.exit(1)

    logger.info(f"Found {len(camera_files)} camera feeds: {list(camera_files.keys())}")

    # 2. Audio Synchronization
    logger.info("Step 1/4: Audio Synchronization...")
    sync_engine = AudioSynchronizer()
    sync_results = sync_engine.synchronize_cameras(camera_files)

    timeline = MasterTimeline()
    for cam_id, info in sync_results.items():
        timeline.add_track(
            camera_id=cam_id,
            file_path=info["file"],
            offset_sec=info["offset_sec"],
            duration=info["duration"]
        )

    # 3. Multi-Modal Motion & Audio Loudness Estimation
    logger.info("Step 2/4: Multi-Modal AI (Visual Motion + Audio Loudness & Applause Analysis)...")
    motion_analyzer = MotionAnalyzer()
    motion_map = motion_analyzer.get_multi_camera_motion_map(
        {k: v["file"] for k, v in sync_results.items()},
        timeline.total_duration
    )

    from selection.audio_analysis import AudioLoudnessAnalyzer
    audio_analyzer = AudioLoudnessAnalyzer()
    audio_map = audio_analyzer.get_multi_camera_audio_map(
        {k: v["file"] for k, v in sync_results.items()},
        timeline.total_duration
    )
    applause_peaks = audio_analyzer.detect_applause_spikes(audio_map)
    logger.info(f"Detected {len(applause_peaks)} audience applause volume surges across audio tracks.")

    selector = CameraSelector()
    edl_segments = selector.generate_edl(timeline, motion_map, audio_map=audio_map, transcribe_subtitles=True)

    edl_json_path = config.DEFAULT_EDL_JSON_PATH
    edl_csv_path = config.DEFAULT_EDL_CSV_PATH
    EDLManager.save_edl_json(edl_segments, str(edl_json_path))
    EDLManager.save_edl_csv(edl_segments, str(edl_csv_path))
    sub_count = sum(1 for seg in edl_segments if seg.get("subtitle"))
    logger.info(f"Step 3/4: Generated Dual EDLs ({len(edl_segments)} segments, {sub_count} transcribed subtitles) -> JSON: {edl_json_path} | CSV: {edl_csv_path}")


    # Validate EDL
    valid, msg = EDLManager.validate_edl(edl_segments)
    logger.info(f"EDL Validation: {msg}")

    # 4. Render Video
    logger.info("Step 4/4: MoviePy Video Rendering...")
    out_name = "final_draft.mp4" if draft_mode else "final.mp4"
    output_mp4 = config.OUTPUT_DIR / out_name
    renderer = MoviePyRenderer()
    success = renderer.render_edl(edl_segments, timeline, str(output_mp4), draft_mode=draft_mode)

    if success:
        logger.info(f"=== PIPELINE COMPLETED SUCCESSFULLY! Output: {output_mp4} ===")
    else:
        logger.error("=== PIPELINE RENDERING FAILED ===")
        sys.exit(1)

def run_gui_app():
    """Launch PySide6 Graphical Interface."""
    from PySide6.QtWidgets import QApplication
    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

def main():
    parser = argparse.ArgumentParser(description="BTIS3053 AI-Assisted Multi-Camera Kindergarten Graduation Video Editor")
    parser.add_argument("--cli", action="store_true", help="Run automated pipeline in headless CLI mode")
    parser.add_argument("--draft", action="store_true", help="Enable fast low-resource 480p @ 15fps draft render mode")
    args = parser.parse_args()

    if args.cli:
        run_cli_pipeline(draft_mode=args.draft)
    else:
        run_gui_app()


if __name__ == "__main__":
    main()
