"""
Human Review & EDL Editing Dialog/Window.
Provides interactive table interface for human review and manual override before final rendering.
"""
import os
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QMessageBox, QHeaderView, QFileDialog
)
from PySide6.QtCore import Qt
from typing import List, Dict, Any

import config
from edl.edl_manager import EDLManager
from ui.video_player import VideoPreviewWidget

logger = logging.getLogger(__name__)


class EDLReviewDialog(QDialog):
    def __init__(self, edl_segments: List[Dict[str, Any]], camera_files: Dict[str, str] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Human Review - Edit Decision List (EDL)")
        self.setMinimumSize(1050, 520)
        self.resize(1150, 600)
        self.edl_segments = [dict(s) for s in edl_segments] # Copy
        self.camera_files = camera_files or {}

        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header Info Banner
        total_dur = sum(seg.get("end_sec", 0.0) - seg.get("start_sec", 0.0) for seg in self.edl_segments) if self.edl_segments else 0.0
        header = QLabel(
            "★ SEMI-AUTOMATED HUMAN REVIEW STEP ★\n"
            f"Review & edit camera angles, timecodes, transitions, and AI reasons. Click any row to preview cut.\n"
            f"Total Output EDL Duration: {total_dur:.1f}s"
        )
        header.setStyleSheet("font-weight: bold; color: #f59e0b; background-color: #1e293b; padding: 10px; border-radius: 5px;")
        layout.addWidget(header)

        # Main Split Content Layout (Left: Table, Right: Video Player)
        split_layout = QHBoxLayout()

        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Seg #", "Start (s)", "End (s)", "Camera Angle", "Transition", "AI Decision Reason"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        split_layout.addWidget(self.table, stretch=6)

        # Embedded Video Player
        self.preview_player = VideoPreviewWidget()
        split_layout.addWidget(self.preview_player, stretch=4)

        layout.addLayout(split_layout)


        # Buttons Toolbar
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("➕ Add Cut Segment")
        self.btn_add.clicked.connect(self._add_row)
        btn_layout.addWidget(self.btn_add)

        self.btn_delete = QPushButton("🗑️ Delete Selected Cut")
        self.btn_delete.clicked.connect(self._delete_row)
        btn_layout.addWidget(self.btn_delete)

        self.btn_export_csv = QPushButton("📊 Export CSV")
        self.btn_export_csv.clicked.connect(self._export_csv)
        btn_layout.addWidget(self.btn_export_csv)

        self.btn_load_edl = QPushButton("📂 Load External EDL")
        self.btn_load_edl.clicked.connect(self._load_edl)
        btn_layout.addWidget(self.btn_load_edl)

        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("✅ Approve & Save EDL")
        self.btn_save.setStyleSheet("background-color: #10b981; font-weight: bold; color: white; padding: 6px 16px;")
        self.btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)


    def _populate_table(self):
        self.table.setRowCount(0)
        for idx, seg in enumerate(self.edl_segments):
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Seg #
            item_num = QTableWidgetItem(str(idx + 1))
            item_num.setFlags(item_num.flags() ^ Qt.ItemIsEditable)
            self.table.setItem(row, 0, item_num)

            # Start (s)
            item_start = QTableWidgetItem(str(seg.get("start_sec", 0.0)))
            self.table.setItem(row, 1, item_start)

            # End (s)
            item_end = QTableWidgetItem(str(seg.get("end_sec", 0.0)))
            self.table.setItem(row, 2, item_end)

            # Camera Angle ComboBox
            cam_combo = QComboBox()
            cam_combo.addItems(config.CAMERA_KEYS)
            cam_combo.setCurrentText(seg.get("camera", "Camera1"))
            self.table.setCellWidget(row, 3, cam_combo)

            # Transition ComboBox
            trans_combo = QComboBox()
            trans_combo.addItems(getattr(config, "TRANSITION_TYPES", ["crossfade", "fade", "cut"]))
            trans_combo.setCurrentText(seg.get("transition", "crossfade"))
            self.table.setCellWidget(row, 4, trans_combo)

            # AI Decision Reason
            item_reason = QTableWidgetItem(seg.get("reason", "Manual adjustment"))
            self.table.setItem(row, 5, item_reason)

    def _add_row(self):
        last_end = 0.0
        if self.edl_segments:
            last_end = self.edl_segments[-1].get("end_sec", 0.0)

        new_seg = {
            "segment_id": len(self.edl_segments) + 1,
            "start_sec": last_end,
            "end_sec": last_end + 5.0,
            "start": "00:00:00",
            "end": "00:00:05",
            "camera": "Camera1",
            "transition": "crossfade",
            "reason": "Human manual addition"
        }
        self.edl_segments.append(new_seg)
        self._populate_table()

    def _delete_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self.edl_segments):
            self.edl_segments.pop(current_row)
            self._populate_table()

    def _on_save(self):
        updated_segments = []
        try:
            for row in range(self.table.rowCount()):
                seg_id = int(self.table.item(row, 0).text())
                start_sec = float(self.table.item(row, 1).text())
                end_sec = float(self.table.item(row, 2).text())
                cam = self.table.cellWidget(row, 3).currentText()
                trans = self.table.cellWidget(row, 4).currentText()
                reason = self.table.item(row, 5).text()

                updated_segments.append({
                    "segment_id": row + 1,
                    "start_sec": round(start_sec, 2),
                    "end_sec": round(end_sec, 2),
                    "start": f"{int(start_sec)//3600:02d}:{(int(start_sec)%3600)//60:02d}:{int(start_sec)%60:02d}",
                    "end": f"{int(end_sec)//3600:02d}:{(int(end_sec)%3600)//60:02d}:{int(end_sec)%60:02d}",
                    "camera": cam,
                    "transition": trans,
                    "reason": reason
                })

            self.edl_segments = updated_segments
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Input", f"Please enter valid numeric start/end values: {e}")

    def _export_csv(self):
        csv_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export EDL to CSV",
            str(config.DEFAULT_EDL_CSV_PATH),
            "CSV Files (*.csv)"
        )
        if csv_path:
            if EDLManager.save_edl_csv(self.edl_segments, csv_path):
                QMessageBox.information(self, "Export Successful", f"Exported EDL to CSV:\n{csv_path}")

    def _load_edl(self):
        edl_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load External EDL File",
            str(config.EDL_DIR),
            "EDL Files (*.json *.csv);;JSON Files (*.json);;CSV Files (*.csv)"
        )
        if edl_path:
            segments = EDLManager.load_edl(edl_path)
            if segments:
                self.edl_segments = segments
                self._populate_table()
                QMessageBox.information(self, "Load Successful", f"Loaded {len(segments)} segments from:\n{edl_path}")
            else:
                QMessageBox.warning(self, "Load Failed", f"Could not parse valid EDL segments from:\n{edl_path}")

    def _find_video_path(self, cam_id: str) -> str:
        """Find video file path for a camera angle with multi-folder and naming fallback."""
        # 1. Direct key match
        if cam_id in self.camera_files and os.path.exists(self.camera_files[cam_id]):
            return self.camera_files[cam_id]

        # 2. Case-insensitive key match in camera_files
        for k, v in self.camera_files.items():
            if k.lower() == cam_id.lower() and os.path.exists(v):
                return v

        # 3. Auto-detect in videos/ directory and subdirectories
        search_dirs = [config.VIDEOS_DIR, config.VIDEOS_DIR / "videoKindergarden"]
        cam_num = "".join(filter(str.isdigit, cam_id)) or "1"

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for entry in search_dir.iterdir():
                if entry.is_file() and entry.suffix.lower() in [".mp4", ".mts", ".mov", ".m2ts", ".avi"]:
                    stem_clean = entry.stem.lower().replace(" ", "").replace("_", "")
                    if f"camera{cam_num}" in stem_clean or f"cam{cam_num}" in stem_clean:
                        return str(entry)

        return ""

    def _on_table_selection_changed(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.edl_segments):
            return

        try:
            start_sec = float(self.table.item(row, 1).text())
            end_sec = float(self.table.item(row, 2).text())
            cam_combo = self.table.cellWidget(row, 3)
            cam_id = cam_combo.currentText() if cam_combo else "Camera1"

            video_path = self._find_video_path(cam_id)

            if video_path and os.path.exists(video_path):
                self.preview_player.play_segment(
                    video_path=video_path,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    label=cam_id
                )
            else:
                self.preview_player.lbl_status.setText(f"❌ No video file found for {cam_id}")
        except Exception as e:
            logger.error(f"Error in preview table selection: {e}")


