"""
Subtitle and Title card overlay generator for MoviePy.
Generates Title Cards, Lower-Third overlays, Subtitles, and Outro Credits.
Uses PIL / Pillow for font rendering to guarantee zero external ImageMagick dependencies.
"""
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    from moviepy import ImageClip, ColorClip, CompositeVideoClip
except ImportError:
    from moviepy.editor import ImageClip, ColorClip, CompositeVideoClip

import config

logger = logging.getLogger(__name__)

def _get_font(font_size: int) -> ImageFont.ImageFont:
    """Attempt to load a font supporting Unicode & Chinese CJK characters (Microsoft YaHei, SimHei, Arial)."""
    font_candidates = [
        "msyh.ttc",       # Microsoft YaHei (Windows Chinese)
        "msyh.ttf",
        "simhei.ttf",     # SimHei (Windows Chinese)
        "simsun.ttc",     # SimSun (Windows Chinese)
        "arial.ttf",      # Standard Arial
    ]
    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, font_size)
        except IOError:
            continue
    return ImageFont.load_default()

class SubtitleGenerator:
    def __init__(self, resolution: tuple[int, int] = config.DEFAULT_RESOLUTION):
        self.width, self.height = resolution

    def _create_pil_text_image(
        self,
        text: str,
        size: tuple[int, int],
        font_size: int = 36,
        text_color: tuple[int, int, int, int] = (255, 255, 255, 255),
        bg_color: tuple[int, int, int, int] = (0, 0, 0, 180),
        subtitle_text: str = None
    ) -> np.ndarray:
        """Create RGBA numpy array containing styled text box with CJK Chinese font support."""
        w, h = size
        img = Image.new("RGBA", (w, h), bg_color)
        draw = ImageDraw.Draw(img)

        font = _get_font(font_size)
        sub_font = _get_font(int(font_size * 0.6))

        # Calculate main text position
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        x = (w - tw) // 2
        y = (h - th) // 2 if not subtitle_text else (h - th) // 2 - 20

        draw.text((x, y), text, font=font, fill=text_color)

        if subtitle_text:
            sub_bbox = draw.textbbox((0, 0), subtitle_text, font=sub_font)
            stw = sub_bbox[2] - sub_bbox[0]
            sx = (w - stw) // 2
            sy = y + th + 15
            draw.text((sx, sy), subtitle_text, font=sub_font, fill=(220, 220, 220, 255))

        return np.array(img)


    def create_title_card(
        self,
        title: str = config.PROJECT_TITLE,
        subtitle: str = config.SCHOOL_NAME,
        duration: float = config.DEFAULT_TITLE_DURATION
    ) -> ImageClip:
        """Create full-screen elegant Opening Title Card clip with silent audio."""
        img_array = self._create_pil_text_image(
            text=title,
            size=(self.width, self.height),
            font_size=42,
            text_color=(255, 215, 0, 255), # Gold text
            bg_color=(15, 23, 42, 255), # Dark slate blue
            subtitle_text=subtitle
        )
        clip = ImageClip(img_array).with_duration(duration) if hasattr(ImageClip, "with_duration") else ImageClip(img_array).set_duration(duration)
        try:
            from moviepy import AudioArrayClip
        except ImportError:
            from moviepy.editor import AudioArrayClip
        silent_audio = AudioArrayClip(np.zeros((int(duration * 44100), 2)), fps=44100)
        if hasattr(clip, "with_audio"):
            clip = clip.with_audio(silent_audio)
        else:
            clip = clip.set_audio(silent_audio)
        return clip

    def create_credits_card(
        self,
        duration: float = config.DEFAULT_CREDITS_DURATION
    ) -> ImageClip:
        """Create full-screen Closing Credits Card clip with silent audio."""
        credits_text = "CONGRATULATIONS GRADUATES!"
        credits_sub = (
            "Special thanks to Teachers, Parents & Students\n"
            "BTIS3053 AI-Assisted Multi-Camera Pipeline\n"
            "Human Reviewed & PDPA 2010 Compliant"
        )
        img_array = self._create_pil_text_image(
            text=credits_text,
            size=(self.width, self.height),
            font_size=38,
            text_color=(255, 255, 255, 255),
            bg_color=(15, 23, 42, 255),
            subtitle_text=credits_sub
        )
        clip = ImageClip(img_array).with_duration(duration) if hasattr(ImageClip, "with_duration") else ImageClip(img_array).set_duration(duration)
        try:
            from moviepy import AudioArrayClip
        except ImportError:
            from moviepy.editor import AudioArrayClip
        silent_audio = AudioArrayClip(np.zeros((int(duration * 44100), 2)), fps=44100)
        if hasattr(clip, "with_audio"):
            clip = clip.with_audio(silent_audio)
        else:
            clip = clip.set_audio(silent_audio)
        return clip

    def create_lower_third(
        self,
        camera_label: str,
        reason: str,
        duration: float
    ) -> ImageClip:
        """Create Lower-Third overlay clip positioned at bottom-left corner."""
        w, h = 500, 70
        img = Image.new("RGBA", (w, h), (15, 23, 42, 200)) # Semi-transparent dark box
        draw = ImageDraw.Draw(img)

        # Draw left gold accent bar
        draw.rectangle([0, 0, 8, h], fill=(255, 215, 0, 255))

        title_font = _get_font(20)
        desc_font = _get_font(14)

        draw.text((20, 10), camera_label, font=title_font, fill=(255, 255, 255, 255))
        draw.text((20, 38), f"AI Decision: {reason}", font=desc_font, fill=(200, 200, 200, 255))


        img_array = np.array(img)
        clip = ImageClip(img_array)

        # Position at bottom-left corner
        pos = (30, self.height - 100)
        if hasattr(clip, "with_duration"):
            clip = clip.with_duration(duration).with_position(pos)
        else:
            clip = clip.set_duration(duration).set_position(pos)

        return clip
