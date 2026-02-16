import requests
import logging
from app.core.config import get_user_settings

logger = logging.getLogger(__name__)

class RadarrClient:
    def __init__(self):
        self.settings = get_user_settings()
        self.url = self.settings.radarr.url.rstrip('/')
        self.api_key = self.settings.radarr.api_key

    def _get_headers(self):
        return {'X-Api-Key': self.api_key}

    def test_connection(self):
        if not self.url or not self.api_key: return False
        try:
            return requests.get(f"{self.url}/api/v3/system/status", headers=self._get_headers(), timeout=5).status_code == 200
        except: return False

    def get_all_movies(self):
        """Get all movies from Radarr"""
        if not self.url or not self.api_key: return []
        try:
            response = requests.get(f"{self.url}/api/v3/movie", headers=self._get_headers(), timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch movies: {e}")
            return []

    def get_all_tags(self):
        if not self.url or not self.api_key: return []
        try:
            response = requests.get(f"{self.url}/api/v3/tag", headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except: return []

    def update_movie(self, movie_data):
        try:
            mid = movie_data.get('id')
            requests.put(f"{self.url}/api/v3/movie/{mid}", json=movie_data, headers=self._get_headers()).raise_for_status()
            return True
        except: return False

def get_radarr_client():
    return RadarrClient()
