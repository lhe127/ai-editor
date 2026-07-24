"""
Rule engine for semi-automated camera selection.
Applies university assignment heuristics to select optimal camera angles.
"""
from typing import Dict, List, Tuple
import config

class RuleEngine:
    def __init__(self, min_shot_duration: float = config.MIN_SHOT_DURATION, max_shot_duration: float = config.MAX_SHOT_DURATION):
        self.min_shot_duration = min_shot_duration
        self.max_shot_duration = max_shot_duration

    def select_camera_for_interval(
        self,
        timestamp: float,
        available_cams: List[str],
        motion_map: Dict[str, List[float]],
        current_cam: str,
        current_shot_length: float,
        sample_interval: float = 0.5
    ) -> Tuple[str, str]:
        """
        Determine which camera to select at a given timestamp.
        Returns tuple of (selected_camera_id, reason_string).
        """
        if not available_cams:
            return current_cam or "Camera1", "Default fallback"

        # Calculate sample index
        sample_idx = int(timestamp / sample_interval)

        # Rule 1: Minimum Shot Duration constraint - maintain current shot if below min threshold
        if current_cam in available_cams and current_shot_length < self.min_shot_duration:
            return current_cam, f"Maintaining shot continuity (min duration {self.min_shot_duration}s)"

        # Rule 2: Force camera switch if shot exceeds max duration to keep video dynamic
        force_switch = current_shot_length >= self.max_shot_duration

        # Calculate motion scores for available cameras at this timestamp
        cam_scores = {}
        for cam_id in available_cams:
            scores = motion_map.get(cam_id, [])
            if 0 <= sample_idx < len(scores):
                cam_scores[cam_id] = scores[sample_idx]
            else:
                cam_scores[cam_id] = 0.0

        # Sort cameras by highest motion score
        sorted_by_motion = sorted(cam_scores.items(), key=lambda x: x[1], reverse=True)
        top_motion_cam, highest_score = sorted_by_motion[0]

        # Rule 3: If highest motion camera is significantly higher than current, switch to it
        current_score = cam_scores.get(current_cam, 0.0)
        if top_motion_cam != current_cam and (highest_score > current_score * 1.3 or force_switch):
            reason = f"High motion activity detected ({highest_score:.1f})" if not force_switch else "Periodic camera angle rotation"
            return top_motion_cam, reason

        # Rule 4: Default to Wide angle (Camera1) or Close-up (Camera2) if available
        if current_cam in available_cams:
            return current_cam, "Stable focus on main performance"
        elif "Camera1" in available_cams:
            return "Camera1", "Front stage wide view"
        else:
            return available_cams[0], "Available camera angle"
