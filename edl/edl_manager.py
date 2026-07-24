"""
EDL Manager module for reading, writing, validating, and updating JSON EDL files.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EDLManager:
    @staticmethod
    def save_edl(edl_segments: List[Dict[str, Any]], filepath: str) -> bool:
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
    def load_edl(filepath: str) -> List[Dict[str, Any]]:
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
    def validate_edl(edl_segments: List[Dict[str, Any]]) -> tuple[bool, str]:
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
