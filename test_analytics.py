import pytest
from datetime import datetime, timezone
from src.models import ChannelData, Video, VideoMetrics
from src.analytics import AnalyticsEngine

def test_proxy_score_never_exceeds_100():
    # Setup mock data with a massive viral outlier
    engine = AnalyticsEngine()
    metrics1 = VideoMetrics(view_count=5000000, engagement_rate=15.0)
    metrics2 = VideoMetrics(view_count=1000, engagement_rate=2.0)
    
    v1 = Video(video_id="1", title="Viral", url="", published_at=datetime.now(timezone.utc), metrics=metrics1)
    v2 = Video(video_id="2", title="Normal", url="", published_at=datetime.now(timezone.utc), metrics=metrics2)
    
    data = ChannelData(channel_name="Test", channel_handle="@Test", average_engagement_rate=5.0, videos=[v1, v2])
    
    # Execution
    scored_data = engine.calculate_scores(data)
    
    # Assertion
    assert scored_data.videos[0].metrics.proxy_score <= 100.0
    assert scored_data.videos[1].metrics.proxy_score <= 100.0

def test_trend_direction_calculation():
    engine = AnalyticsEngine()
    videos = []
    # Create 10 videos where the first 5 (newest) have higher engagement
    for i in range(10):
        eng = 10.0 if i < 5 else 2.0
        v = Video(video_id=str(i), title="", url="", published_at=datetime.now(timezone.utc), metrics=VideoMetrics(engagement_rate=eng))
        videos.append(v)

    data = ChannelData(channel_name="Test", channel_handle="@Test", videos=videos)
    scored_data = engine.calculate_scores(data)

    assert scored_data.trend.direction == "improving"
    assert scored_data.trend.engagement_change_pct > 0