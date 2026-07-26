"""
MoviePy Video Renderer engine.
Parses JSON EDL, applies camera offsets, adds intro/outro cards, applies transitions,
and renders the final MP4 video file.
"""
import os
import logging
from typing import List, Dict, Any

try:
    from moviepy import VideoFileClip, CompositeVideoClip, concatenate_videoclips
    import moviepy.video.fx as vfx
except ImportError:
    from moviepy.editor import VideoFileClip, CompositeVideoClip, concatenate_videoclips
    import moviepy.video.fx.all as vfx

import config
from synchronization.timeline import MasterTimeline
from subtitle.subtitle_generator import SubtitleGenerator

logger = logging.getLogger(__name__)

def helper_subclip(clip, t_start: float, t_end: float):
    """Cross-version MoviePy subclip compatibility."""
    dur = float(clip.duration) if clip.duration is not None else 60.0
    t_start = max(0.0, min(t_start, dur - 0.2))
    t_end = max(t_start + 0.1, min(t_end, dur))

    if hasattr(clip, "subclipped"):
        return clip.subclipped(t_start, t_end)
    elif hasattr(clip, "subclip"):
        return clip.subclip(t_start, t_end)
    return clip

def helper_with_duration(clip, duration: float):
    """Cross-version MoviePy duration compatibility."""
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    elif hasattr(clip, "set_duration"):
        return clip.set_duration(duration)
    return clip

def helper_with_start(clip, start_time: float):
    """Cross-version MoviePy start time compatibility."""
    if hasattr(clip, "with_start"):
        return clip.with_start(start_time)
    elif hasattr(clip, "set_start"):
        return clip.set_start(start_time)
    return clip

def helper_crossfadein(clip, duration: float):
    """Cross-version MoviePy crossfadein compatibility."""
    try:
        if hasattr(vfx, "crossfadein"):
            return vfx.crossfadein(clip, duration)
        elif hasattr(clip, "crossfadein"):
            return clip.crossfadein(duration)
        elif hasattr(vfx, "fadein"):
            return vfx.fadein(clip, duration)
    except Exception:
        pass
    return clip

class MoviePyRenderer:
    def __init__(self, output_resolution: tuple[int, int] = config.DEFAULT_RESOLUTION, fps: int = config.DEFAULT_FPS):
        self.resolution = output_resolution
        self.fps = fps
        self.subtitle_gen = SubtitleGenerator(resolution=output_resolution)

    def render_edl(
        self,
        edl_segments: List[Dict[str, Any]],
        timeline: MasterTimeline,
        output_path: str = str(config.OUTPUT_DIR / "final.mp4"),
        include_title: bool = True,
        include_outro: bool = True,
        progress_callback=None
    ) -> bool:
        """
        Render final video from EDL and MasterTimeline using smooth cross-dissolve transitions.
        """
        if not edl_segments:
            logger.error("Empty EDL segments list. Cannot render.")
            return False

        logger.info(f"Beginning MoviePy video rendering pipeline to {output_path}...")
        processed_items = []
        open_video_clips = []

        try:
            # 1. Add Opening Title Card
            if include_title:
                logger.info("Generating Opening Title Card...")
                title_clip = self.subtitle_gen.create_title_card()
                processed_items.append({
                    "clip": title_clip,
                    "transition": "fade"
                })

            # 2. Process each EDL segment
            total_segments = len(edl_segments)
            for idx, seg in enumerate(edl_segments):
                if progress_callback:
                    progress_callback(int((idx / total_segments) * 80))

                cam_id = seg["camera"]
                start_sec = seg["start_sec"]
                end_sec = seg["end_sec"]
                transition = seg.get("transition", "crossfade")
                reason = seg.get("reason", "Camera selection")

                if cam_id not in timeline.tracks:
                    logger.warning(f"Camera track {cam_id} not found in timeline. Skipping segment.")
                    continue

                track = timeline.tracks[cam_id]
                source_start = track.get_source_time(start_sec)
                source_end = track.get_source_time(end_sec)

                logger.info(f"Rendering Segment {idx+1}/{total_segments}: {cam_id} [{source_start:.2f}s - {source_end:.2f}s]")

                # Load source clip
                raw_clip = VideoFileClip(track.file_path)
                open_video_clips.append(raw_clip)

                # Ensure source timestamps fit within actual video duration
                actual_start = max(0.0, min(source_start, raw_clip.duration - 0.1))
                actual_end = max(actual_start + 0.5, min(source_end, raw_clip.duration))

                sub_clip = helper_subclip(raw_clip, actual_start, actual_end)

                # Resize to target resolution if needed
                if sub_clip.size != list(self.resolution):
                    if hasattr(sub_clip, "resized"):
                        sub_clip = sub_clip.resized(self.resolution)
                    elif hasattr(sub_clip, "resize"):
                        sub_clip = sub_clip.resize(self.resolution)

                segment_duration = sub_clip.duration

                # Attach Lower-Third overlay
                cam_label = config.CAMERA_LABELS.get(cam_id, cam_id)
                lower_third = self.subtitle_gen.create_lower_third(
                    camera_label=f"Angle: {cam_label}",
                    reason=reason,
                    duration=min(4.0, segment_duration)
                )

                composite_seg = CompositeVideoClip([sub_clip, lower_third])
                composite_seg = helper_with_duration(composite_seg, segment_duration)
                processed_items.append({
                    "clip": composite_seg,
                    "transition": transition
                })

            # 3. Add Closing Outro Credits Card
            if include_outro:
                logger.info("Generating Closing Outro Credits Card...")
                credits_clip = self.subtitle_gen.create_credits_card()
                processed_items.append({
                    "clip": credits_clip,
                    "transition": "crossfade"
                })

            if not processed_items:
                logger.error("No valid video clips created.")
                return False

            # 4. Composite clips sequentially with seamless cross-dissolve transitions
            logger.info("Compositing master timeline clips with seamless cross-dissolve transitions...")
            positioned_clips = []
            current_t = 0.0

            for idx, item in enumerate(processed_items):
                clip = item["clip"]
                trans = item.get("transition", "crossfade")
                dur = float(clip.duration) if clip.duration is not None else 5.0

                fade_dur = 0.8 if trans == "crossfade" else (0.4 if trans == "fade" else 0.0)

                if idx > 0 and fade_dur > 0 and dur > (fade_dur * 2):
                    start_t = max(0.0, current_t - fade_dur)
                    clip = helper_crossfadein(clip, fade_dur)
                else:
                    start_t = current_t

                clip = helper_with_start(clip, start_t)
                positioned_clips.append(clip)
                current_t = start_t + dur

            final_clip = CompositeVideoClip(positioned_clips, size=self.resolution)
            final_clip = helper_with_duration(final_clip, current_t)

            # 5. Export MP4 file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            logger.info(f"Writing video file to {output_path}...")

            final_clip.write_videofile(
                output_path,
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",
                threads=4,
                logger="bar"
            )

            if progress_callback:
                progress_callback(100)

            logger.info("Video rendering completed successfully!")

            # Cleanup open resources
            final_clip.close()
            for c in open_video_clips:
                c.close()

            return True

        except Exception as e:
            logger.error(f"Error during video rendering: {e}", exc_info=True)
            return False
