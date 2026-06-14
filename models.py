from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TrendData(BaseModel):
    direction: str 
    engagement_change_pct: float

class VideoMetrics(BaseModel):
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    duration_seconds: int = 0
    engagement_rate: float = 0.0

    proxy_score: Optional[float] = None 
    performance_tier: Optional[str] = None 

class Video(BaseModel):
    video_id: str
    title: str
    url: str
    published_at: datetime
    metrics: VideoMetrics

class ChannelData(BaseModel):
    channel_name: str
    channel_handle: str
    channel_id: Optional[str] = None
    videos: List[Video] = Field(default_factory=list)
    average_engagement_rate: float = 0.0
    trend: Optional[TrendData] = None
    top_videos: List[Video] = Field(default_factory=list)
    bottom_videos: List[Video] = Field(default_factory=list)

class Recommendation(BaseModel):
    strategy: str
    rationale: str

class ContentTheme(BaseModel):
    theme_name: str
    performance_status: str 
    reasoning: str

class ReportResult(BaseModel):
    overall_summary: str
    top_performers: str
    underperforming: str
    content_themes: List[ContentTheme]
    actionable_recommendations: List[Recommendation]