import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.models import ChannelData, Video, VideoMetrics
from src.analytics import AnalyticsEngine
from src.agent import ContentOpsAgent

def test_logarithmic_proxy_score_capping():
    engine = AnalyticsEngine()
    
    v1 = Video(video_id="1", title="Viral", url="", published_at=datetime.now(timezone.utc), metrics=VideoMetrics(view_count=5000000, engagement_rate=10.0))
    v2 = Video(video_id="2", title="Normal", url="", published_at=datetime.now(timezone.utc), metrics=VideoMetrics(view_count=1000, engagement_rate=2.0))
    
    data = ChannelData(channel_name="Test", channel_handle="@Test", average_engagement_rate=5.0, videos=[v1, v2])
    scored_data = engine.calculate_scores(data)
    
    assert scored_data.videos[0].metrics.proxy_score <= 100.0
    assert scored_data.videos[1].metrics.proxy_score <= 100.0

def test_cache_layer_persistence(tmp_path):
    import src.cache
    src.cache.CACHE_DIR = str(tmp_path)
    
    cache = src.cache.CacheLayer(ttl_hours=1)
    mock_data = ChannelData(channel_name="CacheTest", channel_handle="@Cache", videos=[])
    
    cache.save_channel_cache("@Cache", mock_data)
    loaded_data = cache.load_channel_cache("@Cache")
    
    assert loaded_data is not None
    assert loaded_data.channel_name == "CacheTest"

def test_agent_initialization_requires_key():
    original_key = os.environ.get("GROQ_API_KEY")
    os.environ.pop("GROQ_API_KEY", None)
    
    with pytest.raises(ValueError):
        ContentOpsAgent()
        
    if original_key: os.environ["GROQ_API_KEY"] = original_key

@patch('src.youtube.build')
def test_youtube_api_fallback_logic(mock_build):
    from src.youtube import YouTubeExtractor
    
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    
    mock_youtube.channels().list().execute.side_effect = [
        Exception("Handle not found"), 
        {"items": [{"snippet": {"title": "Test Channel"}, "contentDetails": {"relatedPlaylists": {"uploads": "UU123"}}}]}
    ]
    
    mock_youtube.search().list().execute.return_value = {
        "items": [{"snippet": {"channelId": "UC123"}}]
    }
    
    os.environ["YOUTUBE_API_KEY"] = "fake_key"
    extractor = YouTubeExtractor()
    
    channel_id, actual_name, uploads_id = extractor._resolve_via_api("@TestHandle")
    
    assert channel_id == "UC123"
    assert uploads_id == "UU123"