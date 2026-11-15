import pytest
from app.services.youtube import YouTubeService

def test_extract_video_id():
    test_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s&feature=shared", "dQw4w9WgXcQ")
    ]
    for raw_input, expected_id in test_cases:
        assert YouTubeService.extract_video_id(raw_input) == expected_id

def test_scrape_channel_rss_structure():
    # Empty string or handle returns safe list
    result = YouTubeService.scrape_channel_feed_rss("@testchannel")
    assert isinstance(result, list)
