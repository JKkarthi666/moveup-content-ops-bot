import os
import json
from datetime import datetime, timedelta, timezone
from src.models import ChannelData

CACHE_DIR = "data/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

class CacheLayer:
    def __init__(self, ttl_hours=1):
        self.ttl_hours = ttl_hours

    def _get_filepath(self, handle: str) -> str:
        clean_handle = handle.replace("@", "")
        return os.path.join(CACHE_DIR, f"{clean_handle}_cache.json")

    def load_channel_cache(self, handle: str) -> ChannelData | None:
        filepath = self._get_filepath(handle)
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cached_time = datetime.fromisoformat(data['cached_at'])
            if cached_time.tzinfo is None:
                 cached_time = cached_time.replace(tzinfo=timezone.utc)
                 
            if datetime.now(timezone.utc) - cached_time > timedelta(hours=self.ttl_hours):
                return None 
                
            return ChannelData.model_validate(data['channel_data'])
        except Exception:
            return None

    def save_channel_cache(self, handle: str, channel_data: ChannelData):
        filepath = self._get_filepath(handle)
        cache_payload = {
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "channel_data": channel_data.model_dump()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cache_payload, f, default=str)