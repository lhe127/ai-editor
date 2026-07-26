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
        self.last_audience_time = -100.0  # Track timestamp of last audience cutaway

    def select_camera_for_interval(
        self,
        timestamp: float,
        available_cams: List[str],
        motion_map: Dict[str, List[float]],
        current_cam: str,
        current_shot_length: float,
        previous_cam: str = None,
        sample_interval: float = 0.5
    ) -> Tuple[str, str]:
        """
        Determine which camera to select at a given timestamp using multi-camera stage hierarchy rules:
        - Stage Front (Camera1) & Stage Close-up (Camera2) are primary performance shots.
        - Audience Left (Camera3) & Audience Right (Camera4) are brief cutaway reaction shots.
        - Audience reaction shots return back to Stage after 3.5-4s and enforce a 15s cooldown.
        """
        if not available_cams:
            return current_cam or "Camera1", "Default fallback"

        stage_cams = [c for c in available_cams if c in ["Camera1", "Camera2"]]
        audience_cams = [c for c in available_cams if c in ["Camera3", "Camera4"]]

        # Rule 1: Audience Cutaway Return Rule - Audience shots must return to Stage after ~3.5s
        if current_cam in ["Camera3", "Camera4"]:
            if current_shot_length >= 3.5:
                self.last_audience_time = timestamp
                target_stage = "Camera1" if "Camera1" in stage_cams else (stage_cams[0] if stage_cams else "Camera1")
                return target_stage, f"Returning to stage performance ({config.CAMERA_LABELS.get(target_stage, target_stage)})"
            else:
                return current_cam, "Brief audience reaction cutaway"

        # Rule 2: Minimum Stage Shot Duration - Maintain stage shot stability (min 5.0s)
        min_duration = 5.0 if current_cam in stage_cams else self.min_shot_duration
        if current_cam in available_cams and current_shot_length < min_duration:
            return current_cam, f"Maintaining shot continuity (min duration {min_duration:.1f}s)"

        # Calculate motion scores for available cameras at this timestamp
        sample_idx = int(timestamp / sample_interval)
        cam_scores = {}
        for cam_id in available_cams:
            scores = motion_map.get(cam_id, [])
            if 0 <= sample_idx < len(scores):
                cam_scores[cam_id] = scores[sample_idx]
            else:
                cam_scores[cam_id] = 0.0

        current_score = cam_scores.get(current_cam, 0.0)
        force_switch = current_shot_length >= self.max_shot_duration

        # Rule 3: Check for Audience Cutaway (only if cooldown >= 15s has passed)
        if (timestamp - self.last_audience_time) >= 15.0 and audience_cams:
            best_aud = max(audience_cams, key=lambda c: cam_scores.get(c, 0.0))
            aud_score = cam_scores.get(best_aud, 0.0)
            if aud_score > max(current_score * 1.5, 35.0):
                self.last_audience_time = timestamp
                return best_aud, f"Audience reaction cutaway ({config.CAMERA_LABELS.get(best_aud, best_aud)})"

        # Rule 4: Switch between Stage Wide (Camera1) and Stage Close-Up (Camera2) based on performance activity
        if stage_cams:
            best_stage = max(stage_cams, key=lambda c: cam_scores.get(c, 0.0))
            best_stage_score = cam_scores.get(best_stage, 0.0)

            if best_stage != current_cam and (best_stage_score > current_score * 1.25 or force_switch):
                return best_stage, f"Switching to active stage angle: {config.CAMERA_LABELS.get(best_stage, best_stage)}"

        # Rule 5: Default to current stage shot or Stage Front Wide
        if current_cam in available_cams:
            return current_cam, "Stable focus on main stage performance"
        elif "Camera1" in available_cams:
            return "Camera1", "Front stage wide view"
        else:
            return available_cams[0], "Available camera angle"

