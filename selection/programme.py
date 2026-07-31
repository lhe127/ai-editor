"""
Programme schedule parser for BTIS3053 multi-camera video editor pipeline.
Loads programme.csv containing ceremony event intervals and maps timestamps to active events.
"""
import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import config

logger = logging.getLogger(__name__)

def tc_to_seconds(tc_str: str) -> float:
    """Convert HH:MM:SS or MM:SS timecode string to seconds float."""
    try:
        parts = [float(p) for p in tc_str.strip().split(":")]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 1:
            return parts[0]
    except Exception:
        pass
    return 0.0

class ProgrammeManager:
    def __init__(self, csv_path: str = None):
        self.csv_path = Path(csv_path) if csv_path else config.PROGRAMME_CSV_PATH
        self.events: List[Dict[str, Any]] = []
        self.load_programme()

    def load_programme(self) -> List[Dict[str, Any]]:
        """Load ceremony programme schedule from CSV file."""
        if not self.csv_path.exists():
            logger.info(f"Programme CSV not found at {self.csv_path}. Using default stage events.")
            return []

        try:
            self.events = []
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    start_str = row.get("start_time", "00:00:00")
                    end_str = row.get("end_time", "00:00:00")
                    event_name = row.get("event_name", "Ceremony").strip()
                    desc = row.get("description", "").strip()

                    start_sec = tc_to_seconds(start_str)
                    end_sec = tc_to_seconds(end_str)

                    self.events.append({
                        "start_sec": start_sec,
                        "end_sec": end_sec,
                        "event_name": event_name,
                        "description": desc
                    })

            logger.info(f"Successfully loaded {len(self.events)} ceremony events from {self.csv_path}")
            return self.events
        except Exception as e:
            logger.error(f"Failed to parse programme CSV {self.csv_path}: {e}")
            return []

    def get_event_at(self, timestamp_sec: float) -> Optional[Dict[str, Any]]:
        """Find active ceremony event at specified timestamp in seconds."""
        for ev in self.events:
            if ev["start_sec"] <= timestamp_sec < ev["end_sec"]:
                return ev
        return None

    def get_event_title_at(self, timestamp_sec: float) -> str:
        """Get concise event title at timestamp, or empty string if none."""
        ev = self.get_event_at(timestamp_sec)
        return ev["event_name"] if ev else ""
