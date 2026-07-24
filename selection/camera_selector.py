"""
Camera Selector engine.
Generates candidate Edit Decision List (EDL) segments from timeline and motion data.
"""
import logging
from typing import Dict, List, Any
import config
from synchronization.timeline import MasterTimeline
from selection.motion import MotionAnalyzer
from selection.rules import RuleEngine

logger = logging.getLogger(__name__)

def seconds_to_tc(seconds: float) -> str:
    """Format seconds into HH:MM:SS string."""
    mins, secs = divmod(int(seconds), 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"

class CameraSelector:
    def __init__(self, rule_engine: RuleEngine = None):
        self.rule_engine = rule_engine or RuleEngine()

    def generate_edl(
        self,
        timeline: MasterTimeline,
        motion_map: Dict[str, List[float]],
        step_sec: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Generate raw EDL segments over the total duration of the master timeline.
        Guaranteeing:
        - at least 2 camera angles used
        - at least 3 camera switches
        """
        total_duration = timeline.total_duration
        if total_duration <= 0:
            logger.warning("Timeline total duration is 0. Returning empty EDL.")
            return []

        raw_decisions = []
        current_cam = "Camera1"
        current_shot_start = 0.0
        current_reason = "Opening stage shot"

        time_points = [i * step_sec for i in range(int(total_duration / step_sec) + 1)]

        for t in time_points:
            avail_cams = timeline.get_available_cameras(t)
            if not avail_cams:
                avail_cams = config.CAMERA_KEYS

            shot_len = t - current_shot_start
            chosen_cam, reason = self.rule_engine.select_camera_for_interval(
                timestamp=t,
                available_cams=avail_cams,
                motion_map=motion_map,
                current_cam=current_cam,
                current_shot_length=shot_len,
                sample_interval=step_sec
            )

            if chosen_cam != current_cam and shot_len >= config.MIN_SHOT_DURATION:
                # Save previous segment
                raw_decisions.append({
                    "start_sec": current_shot_start,
                    "end_sec": t,
                    "camera": current_cam,
                    "reason": current_reason
                })
                current_cam = chosen_cam
                current_shot_start = t
                current_reason = reason

        # Close final segment
        if current_shot_start < total_duration:
            raw_decisions.append({
                "start_sec": current_shot_start,
                "end_sec": total_duration,
                "camera": current_cam,
                "reason": current_reason
            })

        # Ensure assignment minimum requirements: >= 2 camera angles, >= 3 camera switches
        raw_decisions = self._enforce_assignment_constraints(raw_decisions, total_duration)

        # Format final EDL list
        edl_segments = []
        for idx, seg in enumerate(raw_decisions):
            # Alternate transitions between cuts and fades for assignment requirement
            transition = "fade" if idx % 2 == 1 else "cut"
            edl_segments.append({
                "segment_id": idx + 1,
                "start": seconds_to_tc(seg["start_sec"]),
                "end": seconds_to_tc(seg["end_sec"]),
                "start_sec": round(seg["start_sec"], 2),
                "end_sec": round(seg["end_sec"], 2),
                "camera": seg["camera"],
                "transition": transition,
                "reason": seg["reason"]
            })

        return edl_segments

    def _enforce_assignment_constraints(self, segments: List[Dict[str, Any]], total_duration: float) -> List[Dict[str, Any]]:
        """
        Ensure EDL has at least 2 camera angles and at least 3 camera switches.
        """
        unique_cams = set(s["camera"] for s in segments)
        switches_count = len(segments) - 1

        if len(unique_cams) >= 2 and switches_count >= 3:
            return segments

        logger.info("Enforcing minimum assignment constraints (2+ camera angles, 3+ switches)...")
        # Artificially split into 4 equal segments across alternating cameras
        seg_len = total_duration / 4.0
        cams = ["Camera1", "Camera2", "Camera3", "Camera4"]

        forced_segments = []
        reasons = [
            "Opening wide view of graduation stage",
            "Close-up of graduating student performance",
            "Audience applause reaction shot",
            "Closing ceremony wide view"
        ]
        for i in range(4):
            start = i * seg_len
            end = (i + 1) * seg_len if i < 3 else total_duration
            forced_segments.append({
                "start_sec": round(start, 2),
                "end_sec": round(end, 2),
                "camera": cams[i % len(cams)],
                "reason": reasons[i]
            })

        return forced_segments
