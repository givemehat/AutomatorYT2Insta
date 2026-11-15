import os
import math
from typing import List, Dict, Any, Optional
from app.config import settings

class SubtitleService:
    @staticmethod
    def format_timestamp_ass(seconds: float) -> str:
        """Formats seconds into ASS timestamp: H:MM:SS.cc"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int(round((seconds - math.floor(seconds)) * 100))
        if centis >= 100:
            centis = 99
        return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

    @staticmethod
    def format_timestamp_srt(seconds: float) -> str:
        """Formats seconds into SRT timestamp: HH:MM:SS,mmm"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - math.floor(seconds)) * 1000))
        if millis >= 1000:
            millis = 999
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    @classmethod
    def generate_ass_subtitles(
        cls,
        segments: List[Dict[str, Any]],
        output_file: str,
        style_preset: str = "karaoke_highlight",
        video_width: int = 1080,
        video_height: int = 1920
    ) -> str:
        """
        Generates an Advanced SubStation Alpha (.ass) subtitle file.
        Features large, high-contrast, modern fonts positioned in the lower-third
        with bold outlines and yellow highlight accents designed for Instagram Reels.
        """
        # PrimaryColour: &H00FFFFFF (White), SecondaryColour: &H0000FFFF (Yellow), OutlineColour: &H00000000 (Black)
        ass_header = f"""[Script Info]
Title: AutomatorYT2Insta Reel Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,68,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,2,60,60,320,1
Style: Highlight,Arial Black,72,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,105,105,2,0,1,8,4,2,60,60,320,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for seg in segments:
            start_str = cls.format_timestamp_ass(seg["start"])
            end_str = cls.format_timestamp_ass(seg["end"])
            raw_text = seg.get("text", "").strip()
            if not raw_text:
                continue

            # Split long lines so they fit comfortably on vertical screen
            words = raw_text.split()
            chunk_size = 5
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i+chunk_size])
                # Highlight styling
                if style_preset == "karaoke_highlight":
                    # Highlight first word with yellow accent
                    chunk_words = chunk.split()
                    if len(chunk_words) > 1:
                        formatted_text = f"{{\\c&H0022FFFF&}}{chunk_words[0]}{{\\c&H00FFFFFF&}} " + " ".join(chunk_words[1:])
                    else:
                        formatted_text = f"{{\\c&H0022FFFF&}}{chunk}"
                else:
                    formatted_text = chunk

                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{formatted_text}")

        content = ass_header + "\n".join(events) + "\n"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        return output_file

    @classmethod
    def generate_srt_subtitles(cls, segments: List[Dict[str, Any]], output_file: str) -> str:
        """Generates standard .srt subtitles file."""
        lines = []
        for idx, seg in enumerate(segments, 1):
            start_s = cls.format_timestamp_srt(seg["start"])
            end_s = cls.format_timestamp_srt(seg["end"])
            text = seg.get("text", "").strip()
            lines.append(f"{idx}\n{start_s} --> {end_s}\n{text}\n")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return output_file
