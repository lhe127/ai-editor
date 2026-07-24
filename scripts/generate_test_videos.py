"""
Test Video Generator script.
Generates 4 synthetic camera MP4 files with synchronized audio claps and moving stage graphics
to allow instant end-to-end testing of the editing pipeline without needing real camera hardware.
"""
import os
import sys
import math
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from moviepy import AudioArrayClip, VideoClip, CompositeVideoClip
except ImportError:
    from moviepy.editor import AudioArrayClip, VideoClip, CompositeVideoClip

import config

def make_frame_generator(cam_id: str, color: tuple, label: str, duration: float = 60.0):
    """Generate animated synthetic video frame with motion graphics."""
    width, height = config.DEFAULT_RESOLUTION

    def make_frame(t):
        img = Image.new("RGB", (width, height), color)
        draw = ImageDraw.Draw(img)

        # Draw stage background lines
        draw.rectangle([50, 50, width - 50, height - 50], outline=(255, 255, 255), width=4)
        draw.line([0, height // 2, width, height // 2], fill=(200, 200, 200), width=2)

        # Simulated performer motion (bouncing / oscillating shape)
        cx = int(width / 2 + math.sin(t * 3.0 + (hash(cam_id) % 5)) * 300)
        cy = int(height / 2 + math.cos(t * 2.0) * 150)
        radius = 45

        # Draw bouncing actor
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(255, 215, 0), outline=(255, 255, 255), width=3)

        # Draw Audio Sync Clap Visual Indicator at t=3.0s
        if 2.8 <= t <= 3.2:
            draw.rectangle([0, 0, width, height], fill=(255, 255, 255))
            draw.text((width // 2 - 100, height // 2), "★ CLAP SYNC ★", fill=(255, 0, 0))

        # Text labels
        try:
            font = ImageFont.truetype("arial.ttf", 36)
            sub_font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            font = ImageFont.load_default()
            sub_font = font

        draw.text((80, 80), f"{cam_id}: {label}", font=font, fill=(255, 255, 255))
        draw.text((80, 140), f"Timecode: {t:.2f}s | 1080p 30fps", font=sub_font, fill=(220, 220, 220))

        return np.array(img)

    return make_frame

def generate_sync_audio(offset_sec: float, duration: float = 60.0, sample_rate: int = 44100):
    """Generate audio signal with a distinct beep/clap at t = 3.0s + offset_sec."""
    n_samples = int(duration * sample_rate)
    t_arr = np.linspace(0, duration, n_samples, endpoint=False)

    # Base low background sine tone (220 Hz)
    audio = 0.1 * np.sin(2 * np.pi * 220 * t_arr)

    # Audio Sync Clap Beep (880 Hz burst) at t = 3.0s + offset_sec
    clap_time = 3.0 + offset_sec
    clap_mask = (t_arr >= clap_time) & (t_arr <= clap_time + 0.15)
    audio[clap_mask] += 0.8 * np.sin(2 * np.pi * 880 * t_arr[clap_mask])

    # Convert to stereo array
    stereo_audio = np.vstack([audio, audio]).T
    return AudioArrayClip(stereo_audio, fps=sample_rate)

def main():
    print("=== Generating Synthetic Multi-Camera Test Videos ===")
    config.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    test_cameras = [
        ("Camera1", (30, 41, 59), "Stage Front Wide", 0.0),       # Dark Slate Blue
        ("Camera2", (120, 53, 15), "Stage Center Close-Up", 0.8),  # Warm Crimson
        ("Camera3", (20, 83, 45), "Audience Left Angle", -0.5),   # Forest Green
        ("Camera4", (76, 29, 149), "Audience Right Angle", 0.3)   # Deep Purple
    ]

    duration = 20.0 # 20 seconds test videos for fast rendering

    for cam_id, color, label, offset in test_cameras:
        out_file = config.VIDEOS_DIR / f"{cam_id.lower()}.mp4"
        print(f"Generating {out_file.name} (Simulated Offset: {offset:+.1f}s)...")

        make_frame = make_frame_generator(cam_id, color, label, duration)
        video_clip = VideoClip(make_frame, duration=duration)
        audio_clip = generate_sync_audio(offset_sec=offset, duration=duration)

        if hasattr(video_clip, "with_audio"):
            video_clip = video_clip.with_audio(audio_clip)
        else:
            video_clip = video_clip.set_audio(audio_clip)

        video_clip.write_videofile(
            str(out_file),
            fps=config.DEFAULT_FPS,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )

        video_clip.close()

    print("=== Synthetic Test Videos Generated Successfully in videos/ ===")

if __name__ == "__main__":
    main()
