"""
Audio Loudness & Applause Peak Analyzer for BTIS3053 multi-camera video editing pipeline.
Extracts audio RMS energy, decibels, and detects volume spikes/applause per camera track.
"""
import os
import logging
import numpy as np
from typing import Dict, List, Any

try:
    from moviepy import VideoFileClip
except ImportError:
    from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)

class AudioLoudnessAnalyzer:
    def __init__(self, sample_rate: int = 11025, interval_sec: float = 0.5):
        self.sample_rate = sample_rate
        self.interval_sec = interval_sec

    def analyze_audio_loudness(self, video_path: str, duration: float) -> List[float]:
        """
        Analyze video audio track and return RMS energy scores per interval_sec window.
        """
        if not os.path.exists(video_path):
            n_samples = int(duration / self.interval_sec) + 1
            return [0.0] * n_samples

        try:
            clip = VideoFileClip(video_path)
            if clip.audio is None:
                clip.close()
                n_samples = int(duration / self.interval_sec) + 1
                return [0.0] * n_samples

            sound = clip.audio.to_soundarray(fps=self.sample_rate)
            clip.close()

            if sound.ndim > 1:
                mono = np.mean(sound, axis=1)
            else:
                mono = sound

            samples_per_window = int(self.sample_rate * self.interval_sec)
            loudness_scores = []

            for start_idx in range(0, len(mono), samples_per_window):
                window = mono[start_idx:start_idx + samples_per_window]
                if len(window) > 0:
                    # RMS energy calculation
                    rms = np.sqrt(np.mean(window ** 2))
                    # Scale to 0-100 score range
                    score = float(min(100.0, rms * 500.0))
                    loudness_scores.append(score)
                else:
                    loudness_scores.append(0.0)

            return loudness_scores

        except Exception as e:
            logger.warning(f"Failed audio loudness analysis for {video_path}: {e}")
            n_samples = int(duration / self.interval_sec) + 1
            return [0.0] * n_samples

    def get_multi_camera_audio_map(self, camera_files: Dict[str, str], duration: float) -> Dict[str, List[float]]:
        """
        Compute audio loudness time series for all camera feeds.
        """
        audio_map = {}
        for cam_id, filepath in camera_files.items():
            logger.info(f"Analyzing audio volume & loudness for {cam_id}...")
            scores = self.analyze_audio_loudness(filepath, duration)
            audio_map[cam_id] = scores
        return audio_map

    def detect_applause_spikes(self, audio_map: Dict[str, List[float]], threshold_percentile: float = 85.0) -> List[float]:
        """
        Detect timestamp intervals where audience cameras (Camera 3/4) experience volume spikes.
        Returns list of timestamps in seconds where applause peaks occurred.
        """
        aud_cams = [c for c in ["Camera3", "Camera4"] if c in audio_map]
        if not aud_cams:
            return []

        # Calculate combined audience loudness time series
        max_len = max(len(audio_map[c]) for c in aud_cams)
        combined_loudness = []

        for i in range(max_len):
            scores = [audio_map[c][i] for c in aud_cams if i < len(audio_map[c])]
            combined_loudness.append(np.mean(scores) if scores else 0.0)

        if not combined_loudness or max(combined_loudness) <= 1e-3:
            return []

        threshold = np.percentile(combined_loudness, threshold_percentile)
        applause_timestamps = []

        for idx, val in enumerate(combined_loudness):
            if val >= threshold and val > 15.0: # Minimum audible threshold
                timestamp = idx * self.interval_sec
                applause_timestamps.append(timestamp)

        return applause_timestamps
