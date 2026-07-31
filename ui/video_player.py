"""
Video Preview Player Widget for PySide6 GUI.
Provides embedded video playback, seek controls, and segment boundary looping for Human Review.
"""
import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QStyle
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

logger = logging.getLogger(__name__)

class VideoPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(420, 280)
        self.start_boundary = 0.0
        self.end_boundary = 0.0
        self.current_video_path = ""
        self._pending_seek_ms = None
        self._ignore_position_events = False

        self._setup_ui()
        self._setup_player()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Video Display Widget
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: #020617; border-radius: 6px;")
        self.video_widget.setMinimumHeight(200)
        layout.addWidget(self.video_widget)

        # Segment & Status Label Header
        self.lbl_status = QLabel("🎬 Video Preview: No Clip Loaded")
        self.lbl_status.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.lbl_status)

        # Controls Layout (Play/Pause, Slider, Timecode)
        ctrl_layout = QHBoxLayout()

        self.btn_play = QPushButton("▶️ Play")
        self.btn_play.setFixedWidth(80)
        self.btn_play.clicked.connect(self._toggle_play)
        ctrl_layout.addWidget(self.btn_play)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.sliderMoved.connect(self._on_slider_moved)
        ctrl_layout.addWidget(self.slider)

        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setStyleSheet("color: #e2e8f0; font-family: monospace; font-size: 11px;")
        ctrl_layout.addWidget(self.lbl_time)

        layout.addLayout(ctrl_layout)

    def _setup_player(self):
        try:
            self.player = QMediaPlayer(self)
            self.audio_output = QAudioOutput(self)
            self.audio_output.setVolume(1.0)
            self.player.setAudioOutput(self.audio_output)
            self.player.setVideoOutput(self.video_widget)

            self.player.positionChanged.connect(self._on_position_changed)
            self.player.durationChanged.connect(self._on_duration_changed)
            self.player.mediaStatusChanged.connect(self._on_media_status_changed)
            self.player.errorOccurred.connect(self._on_error_occurred)
        except Exception as e:
            logger.error(f"Failed to initialize QMediaPlayer: {e}")

    def _on_error_occurred(self, error, error_string):
        logger.error(f"QMediaPlayer error [{error}]: {error_string}")
        self.lbl_status.setText(f"❌ Playback Error: {error_string}")

    def _on_media_status_changed(self, status):
        if status in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            if self._pending_seek_ms is not None:
                seek_ms = self._pending_seek_ms
                self._pending_seek_ms = None
                self.player.setPosition(seek_ms)
                self.player.play()
                self.btn_play.setText("⏸️ Pause")
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.btn_play.setText("▶️ Play")

    def load_video(self, video_path: str):
        """Load video file into player."""
        if not os.path.exists(video_path):
            self.lbl_status.setText(f"❌ Video File Not Found: {os.path.basename(video_path)}")
            return

        self.current_video_path = video_path
        self._pending_seek_ms = None
        self.player.setSource(QUrl.fromLocalFile(video_path))
        self.lbl_status.setText(f"📹 Preview: {os.path.basename(video_path)}")

    def play_segment(self, video_path: str, start_sec: float, end_sec: float, label: str = ""):
        """Seek to start_sec and play segment up to end_sec."""
        if not os.path.exists(video_path):
            self.lbl_status.setText(f"❌ File missing: {os.path.basename(video_path)}")
            return

        self._ignore_position_events = True
        self.start_boundary = max(0.0, start_sec)
        self.end_boundary = end_sec
        start_ms = int(self.start_boundary * 1000)

        status_text = f"🎬 Preview: {os.path.basename(video_path)} [{start_sec:.1f}s - {end_sec:.1f}s]"
        if label:
            status_text += f" ({label})"
        self.lbl_status.setText(status_text)

        if self.current_video_path != video_path:
            self.current_video_path = video_path
            self._pending_seek_ms = start_ms
            self.player.setSource(QUrl.fromLocalFile(video_path))
        else:
            self.player.setPosition(start_ms)
            self.player.play()
            self.btn_play.setText("⏸️ Pause")

        self._ignore_position_events = False

    def _toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.btn_play.setText("▶️ Play")
        else:
            self.player.play()
            self.btn_play.setText("⏸️ Pause")

    def _on_position_changed(self, position_ms: int):
        if self._ignore_position_events:
            return

        pos_sec = position_ms / 1000.0
        dur_ms = self.player.duration()

        # Enforce segment end boundary if active
        if self.end_boundary > 0 and pos_sec >= self.end_boundary and pos_sec >= self.start_boundary:
            self.player.pause()
            self.btn_play.setText("▶️ Play")

        if dur_ms > 0:
            val = int((position_ms / dur_ms) * 1000)
            self.slider.setValue(val)

        cur_str = f"{int(pos_sec)//60:02d}:{int(pos_sec)%60:02d}"
        tot_sec = dur_ms / 1000.0 if dur_ms > 0 else 0.0
        tot_str = f"{int(tot_sec)//60:02d}:{int(tot_sec)%60:02d}"
        self.lbl_time.setText(f"{cur_str} / {tot_str}")

    def _on_duration_changed(self, duration_ms: int):
        pass

    def _on_slider_moved(self, value: int):
        dur_ms = self.player.duration()
        if dur_ms > 0:
            target_ms = int((value / 1000.0) * dur_ms)
            self.player.setPosition(target_ms)
