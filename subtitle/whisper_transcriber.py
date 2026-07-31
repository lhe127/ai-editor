"""
Whisper AI Speech Transcription module for automatic Chinese / English subtitle generation.
Integrates OpenAI Whisper for automated speech-to-text captions.
"""
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class WhisperTranscriber:
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model = None

    def _load_model(self):
        if self.model is None:
            try:
                import whisper
                logger.info(f"Loading OpenAI Whisper AI model '{self.model_name}'...")
                self.model = whisper.load_model(self.model_name)
            except ImportError:
                logger.warning("OpenAI Whisper package not installed ('pip install openai-whisper'). Falling back to rule-based captions.")
                self.model = False

    def transcribe_video(self, video_path: str, language: str = "zh") -> List[Dict[str, Any]]:
        """
        Transcribe audio speech from video file into timestamped captions.
        Supports Chinese ('zh') and English ('en').
        """
        if not os.path.exists(video_path):
            return []

        self._load_model()
        if not self.model:
            logger.info("Using ceremony schedule captions fallback.")
            return []

        try:
            logger.info(f"Running Whisper AI speech transcription on {video_path} (Language: {language})...")
            result = self.model.transcribe(video_path, language=language)
            segments = []

            for seg in result.get("segments", []):
                segments.append({
                    "start": float(seg["start"]),
                    "end": float(seg["end"]),
                    "text": str(seg["text"]).strip()
                })

            logger.info(f"Whisper AI transcribed {len(segments)} caption segments.")
            return segments
        except Exception as e:
            logger.error(f"Whisper transcription failed for {video_path}: {e}")
            return []
