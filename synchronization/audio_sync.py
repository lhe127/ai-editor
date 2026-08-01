"""
Audio synchronization engine using cross-correlation of audio signals.
Computes precise time offsets for multi-camera video feeds relative to Camera 1.
"""
import os
import logging
import numpy as np
from scipy import signal

import importlib

try:
    from moviepy import VideoFileClip
except (ImportError, ModuleNotFoundError):
    try:
        _mp_editor = importlib.import_module("moviepy.editor")
        VideoFileClip = _mp_editor.VideoFileClip
    except (ImportError, ModuleNotFoundError):
        from moviepy.video.io.VideoFileClip import VideoFileClip


logger = logging.getLogger(__name__)

class AudioSynchronizer:
    def __init__(self, target_sample_rate: int = 11025):
        self.target_sample_rate = target_sample_rate

    def extract_mono_audio(self, video_path: str) -> tuple[np.ndarray, float]:
        """
        Extract mono audio array and duration from a video file.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        clip = VideoFileClip(video_path)
        duration = clip.duration

        if clip.audio is None:
            clip.close()
            raise ValueError(f"No audio track found in video: {video_path}")

        # Extract audio frames at target sample rate
        # to_soundarray returns shape (n_samples, n_channels)
        audio_array = clip.audio.to_soundarray(fps=self.target_sample_rate)
        clip.close()

        if audio_array.ndim > 1:
            # Convert stereo to mono by averaging channels
            mono = np.mean(audio_array, axis=1)
        else:
            mono = audio_array

        return mono, duration

    def compute_offset(self, ref_audio: np.ndarray, target_audio: np.ndarray) -> float:
        """
        Compute lag offset of target_audio relative to ref_audio in seconds.
        Positive offset means target_audio started AFTER ref_audio (+lag).
        Negative offset means target_audio started BEFORE ref_audio (-lead).
        """
        # Normalize audio arrays
        ref_norm = ref_audio - np.mean(ref_audio)
        target_norm = target_audio - np.mean(target_audio)

        std_ref = np.std(ref_norm)
        std_target = np.std(target_norm)

        if std_ref > 1e-6:
            ref_norm /= std_ref
        if std_target > 1e-6:
            target_norm /= std_target

        # Perform FFT-based cross correlation
        corr = signal.fftconvolve(ref_norm, target_norm[::-1], mode='full')
        lags = signal.correlation_lags(len(ref_norm), len(target_norm), mode='full')

        # Limit correlation search window to max_offset (+/- 10 seconds)
        max_lag_samples = int(10.0 * self.target_sample_rate)
        valid_mask = (lags >= -max_lag_samples) & (lags <= max_lag_samples)

        if np.any(valid_mask):
            corr_window = corr[valid_mask]
            lags_window = lags[valid_mask]
            max_idx = np.argmax(corr_window)
            lag_samples = lags_window[max_idx]
        else:
            max_idx = np.argmax(corr)
            lag_samples = lags[max_idx]

        offset_seconds = lag_samples / float(self.target_sample_rate)
        return float(offset_seconds)

    def synchronize_cameras(self, camera_files: dict[str, str]) -> dict[str, dict]:
        """
        Synchronize multiple camera video files relative to Camera 1.
        Returns dictionary with offset in seconds, offset in ms, and file metadata.
        """
        results = {}
        ref_audio = None
        ref_key = "Camera1"

        if ref_key not in camera_files:
            # Fall back to first available camera if Camera1 is missing
            ref_key = list(camera_files.keys())[0]

        logger.info(f"Using {ref_key} as reference audio anchor.")

        # Extract reference audio
        try:
            ref_audio, ref_duration = self.extract_mono_audio(camera_files[ref_key])
            results[ref_key] = {
                "file": camera_files[ref_key],
                "offset_sec": 0.0,
                "offset_ms": 0,
                "duration": ref_duration,
                "status": "Reference Anchor"
            }
        except Exception as e:
            logger.error(f"Failed to process reference camera {ref_key}: {e}")
            # Fall back to 0 offsets for all
            for cam_id, filepath in camera_files.items():
                results[cam_id] = {
                    "file": filepath,
                    "offset_sec": 0.0,
                    "offset_ms": 0,
                    "duration": 0.0,
                    "status": "Failed to extract audio - default 0 offset"
                }
            return results

        # Process other cameras relative to reference
        for cam_id, filepath in camera_files.items():
            if cam_id == ref_key:
                continue

            try:
                target_audio, target_duration = self.extract_mono_audio(filepath)
                offset_sec = self.compute_offset(ref_audio, target_audio)
                offset_ms = int(round(offset_sec * 1000))

                results[cam_id] = {
                    "file": filepath,
                    "offset_sec": offset_sec,
                    "offset_ms": offset_ms,
                    "duration": target_duration,
                    "status": "Synchronized"
                }
                logger.info(f"{cam_id} offset: {offset_ms:+} ms ({offset_sec:+.3f} s)")
            except Exception as e:
                logger.warning(f"Audio sync failed for {cam_id}: {e}")
                results[cam_id] = {
                    "file": filepath,
                    "offset_sec": 0.0,
                    "offset_ms": 0,
                    "duration": 0.0,
                    "status": f"Fallback 0 offset ({str(e)})"
                }

        return results
