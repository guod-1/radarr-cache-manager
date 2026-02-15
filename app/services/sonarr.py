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
        if not self.url or not self.api_key:
            return False
        try:
            response = requests.get(f"{self.url}/api/v3/system/status", headers=self._get_headers(), timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Sonarr connection test failed: {e}")
            return False

    def get_all_shows(self):
        """Fetch all shows with their tags"""
        if not self.url or not self.api_key:
            return []
        try:
            response = requests.get(f"{self.url}/api/v3/series", headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch shows from Sonarr: {e}")
            return []

    def get_all_tags(self):
        """Fetch all tags"""
        if not self.url or not self.api_key:
            return []
        try:
            response = requests.get(f"{self.url}/api/v3/tag", headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch tags from Sonarr: {e}")
            return []

    def update_show(self, show_data):
        """Update a show entry (for tag swapping)"""
        try:
            sid = show_data.get('id')
            response = requests.put(f"{self.url}/api/v3/series/{sid}", json=show_data, headers=self._get_headers())
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to update show {show_data.get('title')}: {e}")
            return False

def get_sonarr_client():
    return SonarrClient()
