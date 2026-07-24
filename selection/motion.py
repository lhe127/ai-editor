"""
Motion analysis engine using OpenCV frame differencing.
Calculates motion activity scores per camera feed over time intervals.
"""
import logging
import cv2
import numpy as np
from typing import Dict, List

logger = logging.getLogger(__name__)

class MotionAnalyzer:
    def __init__(self, sample_interval_sec: float = 0.5):
        self.sample_interval_sec = sample_interval_sec

    def analyze_camera_motion(self, video_path: str, duration: float) -> List[float]:
        """
        Sample video frames every sample_interval_sec and calculate motion magnitude.
        Returns list of motion scores indexed by sample frame.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video for motion analysis: {video_path}")
            # Return dummy low motion if unreadable
            n_samples = int(duration / self.sample_interval_sec) + 1
            return [0.1] * n_samples

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0

        frame_step = int(fps * self.sample_interval_sec)
        if frame_step < 1:
            frame_step = 1

        motion_scores = []
        prev_gray = None

        while cap.isOpened():
            try:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                # Resize frame to 320x180 for fast motion computation
                small_frame = cv2.resize(frame, (320, 180))
                gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (5, 5), 0)

                if prev_gray is not None:
                    # Frame difference magnitude
                    diff = cv2.absdiff(prev_gray, gray)
                    score = float(np.mean(diff))
                    motion_scores.append(score)
                else:
                    motion_scores.append(0.0)

                prev_gray = gray

                # Fast sequential skip without seeking (prevents H.264 slice decode errors)
                for _ in range(frame_step - 1):
                    if not cap.grab():
                        break

            except Exception as e:
                logger.warning(f"Motion analysis frame read error in {video_path}: {e}")
                motion_scores.append(0.1)

        cap.release()
        if not motion_scores:
            n_samples = int(duration / self.sample_interval_sec) + 1
            motion_scores = [0.1] * n_samples

        return motion_scores

    def get_multi_camera_motion_map(self, camera_files: Dict[str, str], duration: float) -> Dict[str, List[float]]:
        """
        Compute motion score time series for all camera files.
        """
        motion_map = {}
        for cam_id, filepath in camera_files.items():
            logger.info(f"Analyzing motion activity for {cam_id}...")
            scores = self.analyze_camera_motion(filepath, duration)
            motion_map[cam_id] = scores
        return motion_map
