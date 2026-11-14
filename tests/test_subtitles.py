import os
import pytest
from app.services.subtitles import SubtitleService

def test_ass_subtitle_generation(tmp_path):
    segments = [
        {"start": 0.0, "end": 2.5, "text": "This is an unbelievable breakthrough in AI"},
        {"start": 2.5, "end": 5.0, "text": "and here is why it matters"}
    ]
    out_file = str(tmp_path / "test.ass")
    generated = SubtitleService.generate_ass_subtitles(segments, out_file, style_preset="karaoke_highlight")
    assert os.path.exists(generated)
    with open(generated, "r", encoding="utf-8") as f:
        content = f.read()
    assert "[Script Info]" in content
    assert "PlayResY: 1920" in content
    assert "Dialogue: 0," in content

def test_srt_subtitle_generation(tmp_path):
    segments = [
        {"start": 1.25, "end": 4.5, "text": "Hello world from Automator"}
    ]
    out_file = str(tmp_path / "test.srt")
    generated = SubtitleService.generate_srt_subtitles(segments, out_file)
    assert os.path.exists(generated)
    with open(generated, "r", encoding="utf-8") as f:
        content = f.read()
    assert "00:00:01,250 --> 00:00:04,500" in content
    assert "Hello world from Automator" in content
