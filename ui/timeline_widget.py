"""
Timeline Visualization Widget.
Renders synchronized multi-camera audio tracks and active EDL cut segments using PySide6.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtCore import Qt, QRectF
from typing import List, Dict, Any

class TimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(240)
        self.tracks = {}
        self.edl_segments = []
        self.total_duration = 60.0

        # Colors for cameras
        self.cam_colors = {
            "Camera1": QColor(30, 144, 255),  # Dodger Blue
            "Camera2": QColor(220, 20, 60),   # Crimson
            "Camera3": QColor(46, 139, 87),   # Sea Green
            "Camera4": QColor(147, 112, 219)  # Medium Purple
        }

    def set_data(self, tracks: dict, edl_segments: List[Dict[str, Any]], total_duration: float = 60.0):
        """Update timeline widget data."""
        self.tracks = tracks
        self.edl_segments = edl_segments
        self.total_duration = max(10.0, total_duration)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # Background fill
        painter.fillRect(0, 0, width, height, QColor(15, 23, 42))

        # Margin settings
        left_margin = 120
        top_margin = 30
        right_margin = 30
        timeline_w = width - left_margin - right_margin

        if timeline_w <= 0:
            return

        # Draw Time Scale Header
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setFont(QFont("Arial", 9))

        step_seconds = max(5.0, self.total_duration / 10.0)
        t = 0.0
        while t <= self.total_duration:
            x = left_margin + int((t / self.total_duration) * timeline_w)
            painter.drawLine(x, top_margin - 5, x, top_margin + 5)
            painter.drawText(x - 15, top_margin - 10, f"{int(t)}s")
            t += step_seconds

        # Draw Camera Alignment Tracks (Rows 1 - 4)
        cams = ["Camera1", "Camera2", "Camera3", "Camera4"]
        row_h = 32
        for idx, cam_id in enumerate(cams):
            y = top_margin + 20 + idx * (row_h + 8)

            # Track Label
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(15, y + 20, cam_id)

            # Track Background Bar
            painter.fillRect(left_margin, y, timeline_w, row_h, QColor(30, 41, 59))

            # Draw offset clip bar if track data exists
            if cam_id in self.tracks:
                tr = self.tracks[cam_id]
                offset_sec = tr.get("offset_sec", 0.0)
                dur = tr.get("duration", self.total_duration)

                start_x = left_margin + int((max(0.0, offset_sec) / self.total_duration) * timeline_w)
                clip_w = int((dur / self.total_duration) * timeline_w)

                color = self.cam_colors.get(cam_id, QColor(100, 100, 100))
                painter.fillRect(start_x, y + 4, max(4, clip_w), row_h - 8, color)

                # Draw offset text label inside bar
                painter.setPen(QColor(255, 255, 255))
                offset_ms = int(round(offset_sec * 1000))
                painter.drawText(start_x + 6, y + 20, f"Offset: {offset_ms:+}ms")

        # Draw Active EDL Cut Track (Row 5 - Master Output Track)
        master_y = top_margin + 20 + len(cams) * (row_h + 8) + 15
        painter.setPen(QColor(255, 215, 0))
        painter.drawText(15, master_y + 20, "★ Master EDL")

        painter.fillRect(left_margin, master_y, timeline_w, row_h + 4, QColor(15, 23, 42))
        painter.setPen(QPen(QColor(255, 215, 0), 2))
        painter.drawRect(left_margin, master_y, timeline_w, row_h + 4)

        for seg in self.edl_segments:
            start_s = seg.get("start_sec", 0.0)
            end_s = seg.get("end_sec", 0.0)
            cam = seg.get("camera", "Camera1")

            sx = left_margin + int((start_s / self.total_duration) * timeline_w)
            sw = int(((end_s - start_s) / self.total_duration) * timeline_w)

            color = self.cam_colors.get(cam, QColor(200, 200, 200))
            painter.fillRect(sx, master_y + 2, max(2, sw - 1), row_h, color)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(sx + 4, master_y + 22, f"{cam} ({seg.get('transition', 'cut')})")
