import requests
import logging
from app.core.config import get_user_settings

logger = logging.getLogger(__name__)

class SonarrClient:
    def __init__(self):
        self.settings = get_user_settings()
        self.url = self.settings.sonarr.url.rstrip('/')
        self.api_key = self.settings.sonarr.api_key

    def _get_headers(self):
        return {'X-Api-Key': self.api_key}

    def test_connection(self):
        if not self.url or not self.api_key: return False
        try:
            return requests.get(f"{self.url}/api/v3/system/status", headers=self._get_headers(), timeout=5).status_code == 200
        except: return False

    def get_all_shows(self):
        if not self.url or not self.api_key: return []
        try:
            response = requests.get(f"{self.url}/api/v3/series", headers=self._get_headers(), timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch shows: {e}")
            return []

    def get_episode_files(self, series_id):
        """Returns actual files on disk for a series"""
        if not self.url or not self.api_key: return []
        try:
            response = requests.get(f"{self.url}/api/v3/episodefile?seriesId={series_id}", headers=self._get_headers(), timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch episodes for series {series_id}: {e}")
            return []

    def get_all_tags(self):
        if not self.url or not self.api_key: return []
        try:
            response = requests.get(f"{self.url}/api/v3/tag", headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except: return []

def get_sonarr_client():
    return SonarrClient()
