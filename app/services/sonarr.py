"""
Sonarr Service

Handles Sonarr API interactions for TV show management
"""

import requests
import logging
from typing import List, Dict, Any, Optional

from app.core.config import get_user_settings

logger = logging.getLogger(__name__)


class SonarrClient:
    """Sonarr API client"""
    
    def __init__(self):
        user_settings = get_user_settings()
        self.base_url = user_settings.sonarr.url.rstrip('/')
        self.api_key = user_settings.sonarr.api_key
        self.headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make API request to Sonarr"""
        url = f"{self.base_url}/api/v3/{endpoint}"
        
        try:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                timeout=5,
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.content else None
        except Exception as e:
            logger.error(f"Sonarr API request failed: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test Sonarr connection"""
        result = self._request('GET', 'system/status')
        return result is not None
    
    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all tags from Sonarr"""
        tags = self._request('GET', 'tag')
        return tags if tags else []
    
    def get_series_ids_by_tag(self, tag_id: int) -> List[int]:
        """Get all series IDs with a specific tag"""
        series = self._request('GET', 'series')
        if not series:
            return []
        
        return [s['id'] for s in series if tag_id in s.get('tags', [])]
    
    def get_series(self, series_id: int) -> Optional[Dict[str, Any]]:
        """Get series details"""
        return self._request('GET', f'series/{series_id}')
    
    def update_series(self, series_id: int, series_data: Dict[str, Any]) -> bool:
        """Update series"""
        result = self._request('PUT', f'series/{series_id}', json=series_data)
        return result is not None
    
    def get_series_files(self, series_id: int) -> List[str]:
        """Get all file paths for a series"""
        files = []
        
        # Get episode files for this series
        episode_files = self._request('GET', 'episodefile', params={'seriesId': series_id})
        if not episode_files:
            return []
        
        for ep_file in episode_files:
            file_path = ep_file.get('path')
            if file_path:
                files.append(file_path)
        
        return files


def get_sonarr_client() -> SonarrClient:
    """Dependency for FastAPI routes"""
    return SonarrClient()
