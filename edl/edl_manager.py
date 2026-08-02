"""
EDL Manager module for reading, writing, validating, and updating JSON and CSV EDL files.
"""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class EDLManager:
    @staticmethod
    def save_edl_json(edl_segments: List[Dict[str, Any]], filepath: str) -> bool:
        """Save EDL segments to JSON file."""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(edl_segments, f, indent=4)
            logger.info(f"Successfully saved EDL JSON to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save EDL JSON to {filepath}: {e}")
            return False

    @staticmethod
    def save_edl_csv(edl_segments: List[Dict[str, Any]], filepath: str) -> bool:
        """Save EDL segments to CSV file compatible with Microsoft Excel."""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            fieldnames = ["segment_id", "start", "end", "start_sec", "end_sec", "camera", "transition", "reason", "subtitle"]
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for seg in edl_segments:
                    writer.writerow({
                        "segment_id": seg.get("segment_id", 0),
                        "start": seg.get("start", "00:00:00"),
                        "end": seg.get("end", "00:00:00"),
                        "start_sec": seg.get("start_sec", 0.0),
                        "end_sec": seg.get("end_sec", 0.0),
                        "camera": seg.get("camera", "Camera1"),
                        "transition": seg.get("transition", "crossfade"),
                        "reason": seg.get("reason", ""),
                        "subtitle": seg.get("subtitle", "")
                    })
            logger.info(f"Successfully saved EDL CSV to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save EDL CSV to {filepath}: {e}")
            return False

    @staticmethod
    def save_edl(edl_segments: List[Dict[str, Any]], filepath: str) -> bool:
        """Save EDL segments auto-routing by extension (.json or .csv)."""
        if filepath.lower().endswith(".csv"):
            return EDLManager.save_edl_csv(edl_segments, filepath)
        return EDLManager.save_edl_json(edl_segments, filepath)

    @staticmethod
    def load_edl_json(filepath: str) -> List[Dict[str, Any]]:
        """Load EDL segments from JSON file."""
        if not Path(filepath).exists():
            logger.warning(f"EDL JSON file not found: {filepath}")
            return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                segments = json.load(f)
            logger.info(f"Loaded {len(segments)} EDL segments from {filepath}")
            return segments
        except Exception as e:
            logger.error(f"Failed to load EDL JSON from {filepath}: {e}")
            return []

    @staticmethod
    def load_edl_csv(filepath: str) -> List[Dict[str, Any]]:
        """Load EDL segments from CSV file."""
        if not Path(filepath).exists():
            logger.warning(f"EDL CSV file not found: {filepath}")
            return []
        try:
            segments = []
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    start_sec = float(row.get("start_sec", 0.0))
                    end_sec = float(row.get("end_sec", 0.0))
                    segments.append({
                        "segment_id": int(row.get("segment_id", idx + 1)),
                        "start": row.get("start", "00:00:00"),
                        "end": row.get("end", "00:00:00"),
                        "start_sec": start_sec,
                        "end_sec": end_sec,
                        "camera": row.get("camera", "Camera1"),
                        "transition": row.get("transition", "crossfade"),
                        "reason": row.get("reason", "CSV Import"),
                        "subtitle": row.get("subtitle", "")
                    })
            logger.info(f"Loaded {len(segments)} EDL segments from CSV {filepath}")
            return segments
        except Exception as e:
            logger.error(f"Failed to load EDL CSV from {filepath}: {e}")
            return []


    @staticmethod
    def load_edl(filepath: str) -> List[Dict[str, Any]]:
        """Load EDL segments auto-routing by extension (.json or .csv)."""
        if filepath.lower().endswith(".csv"):
            return EDLManager.load_edl_csv(filepath)
        return EDLManager.load_edl_json(filepath)

    @staticmethod
    def validate_edl(edl_segments: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validate EDL schema against university assignment requirements:
        - Must have at least 2 camera angles
        - Must have at least 3 camera switches (4 segments)
        - Must contain valid start, end, camera, transition, reason
        """
        if not edl_segments:
            return False, "EDL is empty."

        cameras = set()
        for idx, seg in enumerate(edl_segments):
            for req_key in ["start", "end", "camera", "transition", "reason"]:
                if req_key not in seg:
                    return False, f"Segment {idx+1} is missing required field '{req_key}'."
            cameras.add(seg["camera"])

        if len(cameras) < 2:
            return False, f"EDL must use at least 2 distinct camera angles (found {len(cameras)})."

        if len(edl_segments) < 4:
            return False, f"EDL must have at least 3 camera switches / 4 segments (found {len(edl_segments)})."

        return True, "EDL is valid and satisfies assignment requirements."
