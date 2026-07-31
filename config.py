"""
Configuration settings for BTIS3053 AI-Assisted Multi-Camera Video Editing Pipeline.
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent

# Suppress non-fatal FFmpeg H.264 seek warnings in console
os.environ["IMAGEIO_FFMPEG_LOGLEVEL"] = "error"
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"
VIDEOS_DIR = BASE_DIR / "videos"
EDL_DIR = BASE_DIR / "edl"
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"

# Ensure required directories exist
for dir_path in [VIDEOS_DIR, EDL_DIR, OUTPUT_DIR, ASSETS_DIR, MUSIC_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Programme Schedule & EDL Paths
PROGRAMME_CSV_PATH = ASSETS_DIR / "programme.csv"
DEFAULT_EDL_JSON_PATH = EDL_DIR / "output.json"
DEFAULT_EDL_CSV_PATH = EDL_DIR / "output.csv"


# Default Video Parameters
DEFAULT_FPS = 30
DEFAULT_RESOLUTION = (1280, 720) # Width x Height
DEFAULT_ASPECT_RATIO = "16:9"

# Fast Low-Resource Draft Parameters
DRAFT_FPS = 15
DRAFT_RESOLUTION = (854, 480) # 480p SD for ultra-fast previews


# Camera Source Configuration
CAMERA_KEYS = ["Camera1", "Camera2", "Camera3", "Camera4"]
CAMERA_LABELS = {
    "Camera1": "Stage Front (Wide)",
    "Camera2": "Stage Center (Close-up)",
    "Camera3": "Audience Left",
    "Camera4": "Audience Right"
}

# Rule-Based Selection Settings
DEFAULT_TARGET_DURATION = 90.0 # seconds (assignment default range 60-180s)
TRANSITION_TYPES = ["crossfade", "fade", "cut"]
MIN_SHOT_DURATION = 4.0  # seconds to prevent rapid camera flickering
MAX_SHOT_DURATION = 12.0 # seconds before forcing angle change
MOTION_SAMPLE_INTERVAL = 0.5 # seconds between motion checks

# Project Metadata
PROJECT_TITLE = "Kindergarten Graduation Ceremony 2026"
SCHOOL_NAME = "Sunshine Little Angels Kindergarten"
DEFAULT_TITLE_DURATION = 4.0 # seconds
DEFAULT_CREDITS_DURATION = 4.0 # seconds

# Ethics & Compliance Disclaimers
ETHICS_DISCLAIMER = (
    "This software operates as a SEMI-AUTOMATED assistant for educational purposes.\n"
    "Mandatory Human Review is required before exporting final video files.\n"
    "Ensure parents' written consent & compliance with Malaysia PDPA 2010 regulations."
)
