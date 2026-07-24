"""
Master timeline module.
Maps multi-camera footage onto a unified master timeline using audio sync offsets.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CameraTrack:
    def __init__(self, camera_id: str, file_path: str, offset_sec: float, duration: float):
        self.camera_id = camera_id
        self.file_path = file_path
        self.offset_sec = offset_sec # Offset relative to master 0:00
        self.duration = duration

    @property
    def master_start(self) -> float:
        """Start time on the master timeline."""
        return max(0.0, self.offset_sec)

    @property
    def master_end(self) -> float:
        """End time on the master timeline."""
        return self.master_start + self.duration

    def get_source_time(self, master_time: float) -> float:
        """Convert master timeline time to source video clip time."""
        return master_time - self.offset_sec

    def is_available_at(self, master_time: float) -> bool:
        """Check if camera has valid frames available at given master timeline time."""
        src_time = self.get_source_time(master_time)
        return 0 <= src_time <= self.duration


class MasterTimeline:
    def __init__(self):
        self.tracks: Dict[str, CameraTrack] = {}

    def add_track(self, camera_id: str, file_path: str, offset_sec: float, duration: float):
        """Add a camera track to master timeline."""
        track = CameraTrack(camera_id, file_path, offset_sec, duration)
        self.tracks[camera_id] = track
        logger.info(f"Added timeline track {camera_id}: master [{track.master_start:.2f}s - {track.master_end:.2f}s]")

    @property
    def total_duration(self) -> float:
        """Calculate total overlap duration of synchronized master timeline."""
        if not self.tracks:
            return 0.0
        # Overlap duration where at least reference camera or multiple cameras are active
        starts = [t.master_start for t in self.tracks.values()]
        ends = [t.master_end for t in self.tracks.values()]
        return max(ends) - min(starts)

    def get_available_cameras(self, master_time: float) -> List[str]:
        """Return list of camera IDs available at master_time."""
        return [cam_id for cam_id, track in self.tracks.items() if track.is_available_at(master_time)]

    def get_summary(self) -> List[Dict[str, Any]]:
        """Return formatted summary list for UI rendering."""
        summary = []
        for cam_id, track in self.tracks.items():
            summary.append({
                "camera": cam_id,
                "file": track.file_path,
                "offset_ms": int(round(track.offset_sec * 1000)),
                "master_start": track.master_start,
                "master_end": track.master_end,
                "duration": track.duration
            })
        return summary
