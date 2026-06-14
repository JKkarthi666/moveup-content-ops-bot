import math
from datetime import datetime, timezone
from src.models import ChannelData, TrendData

class AnalyticsEngine:
    def calculate_scores(self, channel_data: ChannelData) -> ChannelData:
        if not channel_data.videos:
            return channel_data

        avg_eng_rate = channel_data.average_engagement_rate if channel_data.average_engagement_rate > 0 else 1.0
        raw_max_views = max((v.metrics.view_count for v in channel_data.videos), default=1)
        max_views = max(raw_max_views, 1)
        
        now = datetime.now(timezone.utc)
        channel_data.videos.sort(key=lambda v: v.published_at, reverse=True)

        if len(channel_data.videos) >= 10:
            recent_5_avg = sum(v.metrics.engagement_rate for v in channel_data.videos[:5]) / 5
            older_5_avg = sum(v.metrics.engagement_rate for v in channel_data.videos[5:]) / 5
            
            change_pct = ((recent_5_avg - older_5_avg) / older_5_avg * 100) if older_5_avg > 0 else 0
            direction = "improving" if change_pct > 5 else "declining" if change_pct < -5 else "stable"
            
            channel_data.trend = TrendData(
                direction=direction,
                engagement_change_pct=round(change_pct, 2)
            )

        for video in channel_data.videos:
            view_score = (math.log(video.metrics.view_count + 1) / math.log(max_views + 1)) * 100
            
            eng_ratio = video.metrics.engagement_rate / avg_eng_rate
            eng_score = 100 * (eng_ratio / (eng_ratio + 1))
            
            days_old = (now - video.published_at).days
            recency_score = max(100 - (days_old * 2), 0) 

            final_score = (0.50 * view_score) + (0.40 * eng_score) + (0.10 * recency_score)
            final_score = max(10.0, min(final_score, 100.0))
            
            video.metrics.proxy_score = round(final_score, 2)
            video.metrics.performance_tier = self._classify_tier(final_score)

        channel_data.videos.sort(key=lambda x: x.metrics.proxy_score, reverse=True)
        if len(channel_data.videos) >= 4:
            channel_data.top_videos = channel_data.videos[:2]
            channel_data.bottom_videos = channel_data.videos[-2:]

        return channel_data

    def _classify_tier(self, score: float) -> str:
        if score >= 65:
            return "Strong"
        elif score >= 40:
            return "Average"
        else:
            return "Underperforming"