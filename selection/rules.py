"""
Rule engine for semi-automated camera selection.
Applies university assignment heuristics to select optimal camera angles.
"""
from typing import Dict, List, Tuple, Optional
import config
from selection.programme import ProgrammeManager

class RuleEngine:
    def __init__(
        self,
        min_shot_duration: float = config.MIN_SHOT_DURATION,
        max_shot_duration: float = config.MAX_SHOT_DURATION,
        programme_mgr: Optional[ProgrammeManager] = None
    ):
        self.min_shot_duration = min_shot_duration
        self.max_shot_duration = max_shot_duration
        self.programme_mgr = programme_mgr or ProgrammeManager()
        self.last_audience_time = -100.0  # Track timestamp of last audience cutaway

    def _format_reason(self, timestamp: float, base_reason: str) -> str:
        """Attach ceremony programme event title prefix if available."""
        event_title = self.programme_mgr.get_event_title_at(timestamp)
        if event_title:
            return f"[{event_title}] {base_reason}"
        return base_reason

    def select_camera_for_interval(
        self,
        timestamp: float,
        available_cams: List[str],
        motion_map: Dict[str, List[float]],
        current_cam: str,
        current_shot_length: float,
        previous_cam: str = None,
        sample_interval: float = 0.5,
        audio_map: Optional[Dict[str, List[float]]] = None
    ) -> Tuple[str, str]:

        """
        Determine which camera to select at a given timestamp using multi-camera stage hierarchy rules:
        - Stage Front (Camera1) & Stage Close-up (Camera2) are primary performance shots.
        - Audience Left (Camera3) & Audience Right (Camera4) are brief cutaway reaction shots.
        - Audience reaction shots return back to Stage after 3.5-4s and enforce a 15s cooldown.
        - Multi-Modal AI combines motion analysis with audio loudness & applause detection.
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
                return target_stage, self._format_reason(timestamp, f"Returning to stage performance ({config.CAMERA_LABELS.get(target_stage, target_stage)})")
            else:
                return current_cam, self._format_reason(timestamp, "Brief audience reaction cutaway")

        # Rule 2: Minimum Stage Shot Duration - Maintain stage shot stability (min 5.0s)
        min_duration = 5.0 if current_cam in stage_cams else self.min_shot_duration
        if current_cam in available_cams and current_shot_length < min_duration:
            return current_cam, self._format_reason(timestamp, f"Maintaining shot continuity (min duration {min_duration:.1f}s)")

        # Calculate Multi-Modal AI scores (70% motion + 30% audio loudness) for available cameras
        sample_idx = int(timestamp / sample_interval)
        cam_scores = {}
        cam_audios = {}

        for cam_id in available_cams:
            m_scores = motion_map.get(cam_id, [])
            motion_val = m_scores[sample_idx] if 0 <= sample_idx < len(m_scores) else 0.0

            audio_val = 0.0
            if audio_map:
                a_scores = audio_map.get(cam_id, [])
                audio_val = a_scores[sample_idx] if 0 <= sample_idx < len(a_scores) else 0.0

            cam_audios[cam_id] = audio_val
            # Multi-Modal Combined Score
            cam_scores[cam_id] = (0.7 * motion_val) + (0.3 * audio_val)

        current_score = cam_scores.get(current_cam, 0.0)
        force_switch = current_shot_length >= self.max_shot_duration

        # Rule 3: Check for Audience Cutaway (Applause spike or motion surge with >= 15s cooldown)
        if (timestamp - self.last_audience_time) >= 15.0 and audience_cams:
            best_aud = max(audience_cams, key=lambda c: cam_scores.get(c, 0.0))
            aud_score = cam_scores.get(best_aud, 0.0)
            aud_loudness = cam_audios.get(best_aud, 0.0)

            # Check if applause peak or motion surge occurred
            if aud_loudness >= 25.0 or aud_score > max(current_score * 1.4, 30.0):
                self.last_audience_time = timestamp
                reason_detail = "Applause peak reaction" if aud_loudness >= 25.0 else f"Audience reaction ({config.CAMERA_LABELS.get(best_aud, best_aud)})"
                return best_aud, self._format_reason(timestamp, reason_detail)

        # Rule 4: Switch between Stage Wide (Camera1) and Stage Close-Up (Camera2) based on performance activity
        if stage_cams:
            best_stage = max(stage_cams, key=lambda c: cam_scores.get(c, 0.0))
            best_stage_score = cam_scores.get(best_stage, 0.0)

            if best_stage != current_cam and (best_stage_score > current_score * 1.25 or force_switch):
                return best_stage, self._format_reason(timestamp, f"Switching to active stage angle: {config.CAMERA_LABELS.get(best_stage, best_stage)}")


        # Rule 5: Default to current stage shot or Stage Front Wide
        if current_cam in available_cams:
            return current_cam, self._format_reason(timestamp, "Stable focus on main stage performance")
        elif "Camera1" in available_cams:
            return "Camera1", self._format_reason(timestamp, "Front stage wide view")
        else:
            return available_cams[0], self._format_reason(timestamp, "Available camera angle")


