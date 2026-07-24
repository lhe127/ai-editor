"""
Human Review & EDL Editing Dialog/Window.
Provides interactive table interface for human review and manual override before final rendering.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt
from typing import List, Dict, Any

import config

class EDLReviewDialog(QDialog):
    def __init__(self, edl_segments: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Human Review - Edit Decision List (EDL)")
        self.setMinimumSize(850, 450)
        self.edl_segments = [dict(s) for s in edl_segments] # Copy

        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header Info Banner
        header = QLabel(
            "★ SEMI-AUTOMATED HUMAN REVIEW STEP ★\n"
            "Review and customize camera angles, timestamps, transitions, and AI reasons before video rendering."
        )
        header.setStyleSheet("font-weight: bold; color: #f59e0b; background-color: #1e293b; padding: 10px; border-radius: 5px;")
        layout.addWidget(header)

        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Seg #", "Start (s)", "End (s)", "Camera Angle", "Transition", "AI Decision Reason"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Buttons Toolbar
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("➕ Add Cut Segment")
        self.btn_add.clicked.connect(self._add_row)
        btn_layout.addWidget(self.btn_add)

        self.btn_delete = QPushButton("🗑️ Delete Selected Cut")
        self.btn_delete.clicked.connect(self._delete_row)
        btn_layout.addWidget(self.btn_delete)

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
            trans_combo.addItems(["cut", "fade"])
            trans_combo.setCurrentText(seg.get("transition", "cut"))
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
            "transition": "cut",
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
