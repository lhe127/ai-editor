"""
Main PySide6 Application Window.
Integrates the complete multi-camera video editing pipeline:
Import -> Synchronize -> Generate EDL -> Human Review -> Render Final MP4.
"""
import os
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QTextEdit, QMessageBox, QGroupBox, QSpinBox, QScrollArea, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal

import config
from synchronization.audio_sync import AudioSynchronizer
from synchronization.timeline import MasterTimeline
from selection.motion import MotionAnalyzer
from selection.camera_selector import CameraSelector
from edl.edl_manager import EDLManager
from renderer.moviepy_renderer import MoviePyRenderer
from ui.timeline_widget import TimelineWidget
from ui.review_window import EDLReviewDialog

logger = logging.getLogger(__name__)

# Worker Threads for non-blocking UI
class SyncWorker(QThread):
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, camera_files: dict):
        super().__init__()
        self.camera_files = camera_files

    def run(self):
        try:
            synchronizer = AudioSynchronizer()
            results = synchronizer.synchronize_cameras(self.camera_files)
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))

class RenderWorker(QThread):
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)

    def __init__(self, edl_segments: list, timeline: MasterTimeline, output_path: str, draft_mode: bool = False):
        super().__init__()
        self.edl_segments = edl_segments
        self.timeline = timeline
        self.output_path = output_path
        self.draft_mode = draft_mode

    def run(self):
        try:
            renderer = MoviePyRenderer()
            success = renderer.render_edl(
                edl_segments=self.edl_segments,
                timeline=self.timeline,
                output_path=self.output_path,
                progress_callback=self.progress_signal.emit,
                draft_mode=self.draft_mode
            )
            self.finished_signal.emit(success, self.output_path)
        except Exception as e:
            self.finished_signal.emit(False, str(e))



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BTIS3053 - AI-Assisted Multi-Camera Graduation Video Editor (Semi-Automated)")
        self.setMinimumSize(960, 680)
        self.resize(1150, 850)

        # Pipeline state
        self.camera_files = {}
        self.timeline = MasterTimeline()
        self.edl_segments = []
        self.sync_results = {}

        self._setup_ui()
        self._auto_detect_videos()

    def _setup_ui(self):
        # Main Scroll Area Wrapper to prevent elements from being hidden on smaller screens
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #0f172a; }")
        self.setCentralWidget(scroll_area)

        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 1. Ethics & Compliance Header Banner
        ethics_box = QGroupBox("University Assignment & Ethics Compliance")
        ethics_layout = QVBoxLayout(ethics_box)
        ethics_label = QLabel(config.ETHICS_DISCLAIMER)
        ethics_label.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")
        ethics_layout.addWidget(ethics_label)
        main_layout.addWidget(ethics_box)

        # 2. Controls & Target Duration Toolbar Group
        control_box = QGroupBox("Video Pipeline Controls & Settings")
        control_box_layout = QVBoxLayout(control_box)

        top_controls = QHBoxLayout()
        target_dur_label = QLabel("⏱️ Target Output Duration (sec):")
        target_dur_label.setStyleSheet("font-weight: bold; color: #f59e0b; font-size: 13px;")
        top_controls.addWidget(target_dur_label)

        self.spin_target_duration = QSpinBox()
        self.spin_target_duration.setRange(15, 600)
        self.spin_target_duration.setValue(int(config.DEFAULT_TARGET_DURATION))
        self.spin_target_duration.setSingleStep(5)
        self.spin_target_duration.setToolTip("Set maximum output video length in seconds (Assignment default: 60-180s)")
        self.spin_target_duration.setStyleSheet("font-size: 13px; font-weight: bold; padding: 3px 8px;")
        top_controls.addWidget(self.spin_target_duration)

        top_controls.addSpacing(25)

        self.chk_draft = QCheckBox("⚡ Draft Mode (Fast 480p preview)")
        self.chk_draft.setToolTip("Enable low-resource fast 480p @ 15fps rendering for quick testing (~5s)")
        self.chk_draft.setStyleSheet("font-weight: bold; color: #38bdf8; font-size: 13px;")
        top_controls.addWidget(self.chk_draft)

        top_controls.addStretch()
        control_box_layout.addLayout(top_controls)


        # Workflow Buttons Toolbar
        toolbar_layout = QHBoxLayout()

        self.btn_import = QPushButton("1. 📁 Import Videos")
        self.btn_import.clicked.connect(self._on_import_videos)
        toolbar_layout.addWidget(self.btn_import)

        self.btn_sync = QPushButton("2. ⏱️ Audio Synchronize")
        self.btn_sync.clicked.connect(self._on_synchronize)
        toolbar_layout.addWidget(self.btn_sync)

        self.btn_gen_edl = QPushButton("3. 🤖 Generate AI EDL")
        self.btn_gen_edl.clicked.connect(self._on_generate_edl)
        toolbar_layout.addWidget(self.btn_gen_edl)

        self.btn_review = QPushButton("4. ✏️ Human Review EDL")
        self.btn_review.clicked.connect(self._on_human_review)
        toolbar_layout.addWidget(self.btn_review)

        self.btn_render = QPushButton("5. 🎬 Render Final MP4")
        self.btn_render.setStyleSheet("background-color: #059669; font-weight: bold; color: white;")
        self.btn_render.clicked.connect(self._on_render_video)
        toolbar_layout.addWidget(self.btn_render)

        self.btn_preview_rendered = QPushButton("6. 📺 Preview Rendered Video")
        self.btn_preview_rendered.setStyleSheet("background-color: #0284c7; font-weight: bold; color: white;")
        self.btn_preview_rendered.clicked.connect(self._on_preview_rendered_video)
        toolbar_layout.addWidget(self.btn_preview_rendered)

        control_box_layout.addLayout(toolbar_layout)
        main_layout.addWidget(control_box)

        # 3. Video Import Status Table
        self.cam_table = QTableWidget()
        self.cam_table.setColumnCount(5)
        self.cam_table.setHorizontalHeaderLabels(["Camera ID", "File Path", "Sync Offset (ms)", "Duration (s)", "Status"])
        self.cam_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cam_table.setFixedHeight(120)
        main_layout.addWidget(self.cam_table)

        # 4. Master Timeline Visualizer
        self.timeline_widget = TimelineWidget()
        self.timeline_widget.setMinimumHeight(220)
        main_layout.addWidget(self.timeline_widget)

        # 5. Progress Bar & Log Output Console
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("background-color: #0f172a; color: #a7f3d0; font-family: Consolas, monospace;")
        self.log_console.setFixedHeight(120)
        main_layout.addWidget(self.log_console)

        self.log_info("System Initialized. Ready to import camera feeds.")

    def log_info(self, message: str):
        """Append log message to UI log console."""
        self.log_console.append(f"> {message}")
        logger.info(message)

    def _auto_detect_videos(self):
        """Auto-detect default sample videos in videos/ directory and subdirectories."""
        auto_found = {}
        search_dirs = [config.VIDEOS_DIR, config.VIDEOS_DIR / "videoKindergarden"]

        for cam_id in config.CAMERA_KEYS:
            cam_num = "".join(filter(str.isdigit, cam_id)) or "1"
            found_path = None
            for s_dir in search_dirs:
                if not s_dir.exists():
                    continue
                for entry in s_dir.iterdir():
                    if entry.is_file() and entry.suffix.lower() in [".mp4", ".mts", ".mov", ".m2ts", ".avi"]:
                        stem_clean = entry.stem.lower().replace(" ", "").replace("_", "")
                        if f"camera{cam_num}" in stem_clean or f"cam{cam_num}" in stem_clean:
                            found_path = str(entry)
                            break
                if found_path:
                    break

            if found_path:
                auto_found[cam_id] = found_path

        if auto_found:
            self.camera_files = auto_found
            self.log_info(f"Auto-detected {len(auto_found)} camera feeds in {config.VIDEOS_DIR}")
            self._update_cam_table()

    def _on_import_videos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Camera Videos (MP4 / MOV / MTS)",
            str(config.VIDEOS_DIR),
            "Video Files (*.mp4 *.mov *.mts *.m2ts);;MTS Files (*.mts *.m2ts);;All Files (*)"
        )
        if files:
            self.camera_files = {}
            for idx, filepath in enumerate(files[:4]):
                cam_id = config.CAMERA_KEYS[idx]
                self.camera_files[cam_id] = filepath

            self.log_info(f"Imported {len(self.camera_files)} camera video feeds.")
            self._update_cam_table()

    def _update_cam_table(self):
        self.cam_table.setRowCount(0)
        for cam_id in config.CAMERA_KEYS:
            row = self.cam_table.rowCount()
            self.cam_table.insertRow(row)

            filepath = self.camera_files.get(cam_id, "Not Selected")
            offset_ms = self.sync_results.get(cam_id, {}).get("offset_ms", 0)
            dur = self.sync_results.get(cam_id, {}).get("duration", 0.0)
            status = self.sync_results.get(cam_id, {}).get("status", "Imported" if cam_id in self.camera_files else "Missing")

            self.cam_table.setItem(row, 0, QTableWidgetItem(cam_id))
            self.cam_table.setItem(row, 1, QTableWidgetItem(os.path.basename(filepath)))
            self.cam_table.setItem(row, 2, QTableWidgetItem(f"{offset_ms:+} ms"))
            self.cam_table.setItem(row, 3, QTableWidgetItem(f"{dur:.1f} s"))
            self.cam_table.setItem(row, 4, QTableWidgetItem(status))

    def _on_synchronize(self):
        if not self.camera_files:
            QMessageBox.warning(self, "No Videos", "Please import camera videos first or run test generator script.")
            return

        self.log_info("Starting audio cross-correlation synchronization...")
        self.progress_bar.setValue(20)

        self.sync_thread = SyncWorker(self.camera_files)
        self.sync_thread.finished_signal.connect(self._on_sync_finished)
        self.sync_thread.error_signal.connect(lambda err: self.log_info(f"Sync Error: {err}"))
        self.sync_thread.start()

    def _on_sync_finished(self, results: dict):
        self.sync_results = results
        self.timeline = MasterTimeline()

        for cam_id, info in results.items():
            if os.path.exists(info["file"]):
                self.timeline.add_track(
                    camera_id=cam_id,
                    file_path=info["file"],
                    offset_sec=info["offset_sec"],
                    duration=info["duration"]
                )

        self.progress_bar.setValue(100)
        self._update_cam_table()
        self.timeline_widget.set_data(results, self.edl_segments, self.timeline.total_duration)
        self.log_info("Audio Synchronization Complete. Master timeline generated.")

    def _on_generate_edl(self):
        if not self.timeline.tracks:
            QMessageBox.warning(self, "Timeline Empty", "Please run Audio Synchronization step first.")
            return

        try:
            target_dur = float(self.spin_target_duration.value())
            self.log_info(f"Running Multi-Modal AI (Motion + Audio Loudness & Speech Subtitle Transcription, Target: {target_dur:.1f}s)...")

            valid_files = {k: v["file"] for k, v in self.sync_results.items() if "file" in v}
            motion_analyzer = MotionAnalyzer()
            motion_map = motion_analyzer.get_multi_camera_motion_map(valid_files, self.timeline.total_duration)

            from selection.audio_analysis import AudioLoudnessAnalyzer
            audio_analyzer = AudioLoudnessAnalyzer()
            audio_map = audio_analyzer.get_multi_camera_audio_map(valid_files, self.timeline.total_duration)

            selector = CameraSelector()
            self.edl_segments = selector.generate_edl(
                self.timeline,
                motion_map,
                target_duration=target_dur,
                audio_map=audio_map,
                transcribe_subtitles=True
            )


            EDLManager.save_edl_json(self.edl_segments, str(config.DEFAULT_EDL_JSON_PATH))
            EDLManager.save_edl_csv(self.edl_segments, str(config.DEFAULT_EDL_CSV_PATH))

            effective_dur = min(self.timeline.total_duration, target_dur) if self.timeline.total_duration > 0 else target_dur
            self.timeline_widget.set_data(self.sync_results, self.edl_segments, effective_dur)
            sub_count = sum(1 for seg in self.edl_segments if seg.get("subtitle"))
            self.log_info(f"Generated {len(self.edl_segments)} EDL cut segments with {sub_count} transcribed subtitle captions. Saved JSON & CSV to {config.EDL_DIR}")



        except Exception as e:
            self.log_info(f"EDL Generation Error: {e}")
            logger.error(f"Error during EDL generation: {e}", exc_info=True)
            QMessageBox.critical(self, "EDL Generation Error", f"An error occurred during EDL generation:\n{e}")

    def _on_human_review(self):
        if not self.edl_segments:
            QMessageBox.warning(self, "No EDL", "Please click 'Generate AI EDL' first.")
            return

        dialog = EDLReviewDialog(self.edl_segments, self.camera_files, self)
        if dialog.exec():

            self.edl_segments = dialog.edl_segments
            edl_json_path = str(config.DEFAULT_EDL_JSON_PATH)
            edl_csv_path = str(config.DEFAULT_EDL_CSV_PATH)
            EDLManager.save_edl_json(self.edl_segments, edl_json_path)
            EDLManager.save_edl_csv(self.edl_segments, edl_csv_path)
            self.timeline_widget.set_data(self.sync_results, self.edl_segments, self.timeline.total_duration)
            self.log_info("EDL successfully updated and approved by Human Reviewer. Saved output.json and output.csv.")

    def _on_render_video(self):
        if not self.edl_segments:
            QMessageBox.warning(self, "No EDL", "Please generate and review EDL before rendering.")
            return

        valid, msg = EDLManager.validate_edl(self.edl_segments)
        if not valid:
            QMessageBox.warning(self, "EDL Validation Failed", msg)
            return

        is_draft = self.chk_draft.isChecked()
        out_name = "final_draft.mp4" if is_draft else "final.mp4"
        out_path = str(config.OUTPUT_DIR / out_name)
        self.log_info(f"Launching MoviePy render pipeline -> {out_path} [Draft Mode: {is_draft}]...")
        self.progress_bar.setValue(5)

        self.render_thread = RenderWorker(self.edl_segments, self.timeline, out_path, draft_mode=is_draft)
        self.render_thread.progress_signal.connect(self.progress_bar.setValue)
        self.render_thread.finished_signal.connect(self._on_render_finished)
        self.render_thread.start()


    def _on_render_finished(self, success: bool, path_or_err: str):
        if success:
            self.progress_bar.setValue(100)
            self.log_info(f"SUCCESS: Rendered final video to {path_or_err}")
            reply = QMessageBox.information(
                self,
                "Render Complete",
                f"Final MP4 video exported to:\n{path_or_err}\n\nWould you like to preview the rendered video now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._open_video_preview_dialog(path_or_err)
        else:
            self.log_info(f"Render Error: {path_or_err}")
            QMessageBox.critical(self, "Render Failed", f"Error during rendering:\n{path_or_err}")

    def _on_preview_rendered_video(self):
        """Open video preview window for rendered video or prompt user to select one."""
        draft_path = config.OUTPUT_DIR / "final_draft.mp4"
        final_path = config.OUTPUT_DIR / "final.mp4"

        target_file = None
        if final_path.exists():
            target_file = str(final_path)
        elif draft_path.exists():
            target_file = str(draft_path)

        if not target_file:
            selected, _ = QFileDialog.getOpenFileName(
                self,
                "Select Video File to Preview",
                str(config.OUTPUT_DIR),
                "Video Files (*.mp4 *.mov *.mts);;All Files (*)"
            )
            if selected:
                target_file = selected

        if target_file:
            self._open_video_preview_dialog(target_file)
        else:
            QMessageBox.warning(self, "No Video Found", "No rendered video file found in output/ directory. Please render a video first.")

    def _open_video_preview_dialog(self, video_path: str):
        """Open modal dialog to play video."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        from ui.video_player import VideoPreviewWidget

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Video Preview - {os.path.basename(video_path)}")
        dialog.resize(800, 520)

        dlg_layout = QVBoxLayout(dialog)
        player = VideoPreviewWidget(dialog)
        dlg_layout.addWidget(player)

        player.load_video(video_path)
        player.player.play()
        player.btn_play.setText("⏸️ Pause")

        dialog.exec()
