import os
import isodate
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.models import Video, VideoMetrics, ChannelData
from src.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

class YouTubeExtractor:
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("Missing YOUTUBE_API_KEY in environment variables.")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def _execute_with_retry(self, request_func):
        try:
            return request_func().execute()
        except HttpError as e:
            if e.resp.status in [403, 429]:
                logger.error("YouTube Quota Limit reached.")
            raise e

    def _resolve_via_api(self, clean_handle: str):
        try:
            req = lambda: self.youtube.channels().list(part="snippet,contentDetails", forHandle=clean_handle)
            res = self._execute_with_retry(req)
            if res.get("items"):
                return res["items"][0]["id"], res["items"][0]["snippet"]["title"], res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        except Exception as e:
            logger.warning(f"forHandle API failed for {clean_handle}: {e}. Falling back to Search API.")

        search_req = lambda: self.youtube.search().list(part="snippet", q=clean_handle, type="channel", maxResults=1)
        search_res = self._execute_with_retry(search_req)
        if not search_res.get("items"):
            raise ValueError(f"Channel {clean_handle} could not be found on YouTube.")
        
        channel_id = search_res["items"][0]["snippet"]["channelId"]
        channel_req = lambda: self.youtube.channels().list(part="snippet,contentDetails", id=channel_id)
        channel_res = self._execute_with_retry(channel_req)
        
        return channel_id, channel_res["items"][0]["snippet"]["title"], channel_res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    def fetch_last_10_videos(self, channel_handle: str) -> ChannelData:
        logger.info(f"Extracting YouTube metrics for {channel_handle}...")
        clean_handle = channel_handle.strip()
        if not clean_handle.startswith("@"): 
            clean_handle = f"@{clean_handle}"

        channel_id, actual_name, uploads_id = self._resolve_via_api(clean_handle)

        try:
            playlist_req = lambda: self.youtube.playlistItems().list(part="snippet,contentDetails", playlistId=uploads_id, maxResults=10)
            playlist_res = self._execute_with_retry(playlist_req)
        except Exception as e:
            logger.warning(f"Failed using cached ID for {clean_handle}. Auto-healing via live API. Error: {e}")
            channel_id, actual_name, uploads_id = self._resolve_via_api(clean_handle)
            playlist_req = lambda: self.youtube.playlistItems().list(part="snippet,contentDetails", playlistId=uploads_id, maxResults=10)
            playlist_res = self._execute_with_retry(playlist_req)

        video_ids = [item["contentDetails"]["videoId"] for item in playlist_res.get("items", [])]
        if not video_ids: 
            return ChannelData(channel_name=actual_name, channel_handle=clean_handle, channel_id=channel_id)

        try:
            video_req = lambda: self.youtube.videos().list(part="snippet,statistics,contentDetails", id=",".join(video_ids))
            video_res = self._execute_with_retry(video_req)
            items = video_res.get("items", [])
        except Exception as e:
            raise ValueError(f"Failed fetching stats: {str(e)}")

        videos = []
        for item in items:
            stats = item.get("statistics", {})
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            
            engagement_rate = ((likes + comments) / views * 100) if views > 0 else 0.0
            duration_sec = int(isodate.parse_duration(item["contentDetails"]["duration"]).total_seconds())
            safe_date = datetime.fromisoformat(item["snippet"]["publishedAt"].replace("Z", "+00:00"))

            metrics = VideoMetrics(view_count=views, like_count=likes, comment_count=comments, duration_seconds=duration_sec, engagement_rate=round(engagement_rate, 2))
            videos.append(Video(video_id=item["id"], title=item["snippet"]["title"], url=f"https://www.youtube.com/watch?v={item['id']}", published_at=safe_date, metrics=metrics))

        avg_eng = sum(v.metrics.engagement_rate for v in videos) / len(videos) if videos else 0
        return ChannelData(channel_name=actual_name, channel_handle=clean_handle, channel_id=channel_id, videos=videos, average_engagement_rate=round(avg_eng, 2))