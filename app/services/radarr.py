"""
Radarr API Client

Handles all interactions with the Radarr API including:
- Fetching movies by tag
- Getting movie details and ratings
- Updating movie tags
"""

import requests
from typing import Optional, List, Dict, Any
import logging

from app.core.config import get_user_settings

logger = logging.getLogger(__name__)


class RadarrClient:
    """Client for interacting with Radarr API"""
    
    def __init__(self):
        self.settings = get_user_settings().radarr
        self.base_url = self.settings.url.rstrip('/')
        self.api_key = self.settings.api_key
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make a request to Radarr API"""
        url = f"{self.base_url}/api/v3/{endpoint.lstrip('/')}"
        headers = {
            'X-Api-Key': self.api_key,
            'accept': 'application/json'
        }
        
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            kwargs.pop('headers')
        
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Radarr API request failed: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test connection to Radarr"""
        try:
            response = self._request('GET', '/system/status')
            return response is not None
        except Exception as e:
            logger.error(f"Failed to connect to Radarr: {e}")
            return False
    
    def get_tag_details(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """Get details for a specific tag including movie IDs"""
        response = self._request('GET', f'/tag/detail/{tag_id}')
        if response:
            return response.json()
        return None
    
    def get_movie_ids_by_tag(self, tag_id: int) -> List[int]:
        """Fetch list of movie IDs with a specific tag"""
        tag_details = self.get_tag_details(tag_id)
        if tag_details:
            return tag_details.get('movieIds', [])
        return []
    
    def get_movie(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get details for a specific movie"""
        response = self._request('GET', f'/movie/{movie_id}')
        if response:
            return response.json()
        return None
    
    def update_movie(self, movie_id: int, movie_data: Dict[str, Any]) -> bool:
        """Update a movie's data"""
        response = self._request(
            'PUT',
            f'/movie/{movie_id}',
            headers={'Content-Type': 'application/json'},
            json=movie_data
        )
        return response is not None
    
    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all tags from Radarr"""
        response = self._request('GET', '/tag')
        if response:
            return response.json()
        return []


class MovieProcessor:
    """Processes movies and manages tags based on ratings"""
    
    def __init__(self):
        self.client = RadarrClient()
        self.settings = get_user_settings()
    
    def get_movie_ratings(self, movie: Dict[str, Any]) -> Dict[str, float]:
        """Extract ratings from movie data"""
        ratings = movie.get('ratings', {})
        return {
            'imdb': ratings.get('imdb', {}).get('value', 0),
            'tmdb': ratings.get('tmdb', {}).get('value', 0),
            'metacritic': ratings.get('metacritic', {}).get('value', 0),
            'rotten_tomatoes': ratings.get('rottenTomatoes', {}).get('value', 0)
        }
    
    def is_high_rating(self, ratings: Dict[str, float]) -> bool:
        """Check if movie meets high-rating thresholds"""
        thresholds = self.settings.thresholds
        return (
            ratings['imdb'] > thresholds.imdb and
            ratings['tmdb'] > thresholds.tmdb and
            ratings['metacritic'] > thresholds.metacritic and
            ratings['rotten_tomatoes'] > thresholds.rotten_tomatoes
        )
    
    def get_movie_file_path(self, movie: Dict[str, Any]) -> Optional[str]:
        """Get the file path for a movie"""
        movie_file = movie.get('movieFile', {})
        return movie_file.get('path') if movie_file else None
    
    def convert_path_to_host(self, plex_path: str) -> str:
        """Convert Plex path to host path using path mappings"""
        for mapping in self.settings.path_mappings:
            if plex_path.startswith(mapping.plex_path):
                return plex_path.replace(mapping.plex_path, mapping.host_path, 1)
        return plex_path
    
    def modify_tags(self, movie: Dict[str, Any], action: str, tag_id: int) -> Dict[str, Any]:
        """Modify tags on a movie"""
        tags = movie.get('tags', [])
        
        if action == "add":
            if tag_id not in tags:
                tags.append(tag_id)
        elif action == "remove":
            if tag_id in tags:
                tags.remove(tag_id)
        elif action == "replace":
            tags = [tag_id]
        
        movie['tags'] = tags
        return movie
    
    def process_movie(self, movie_id: int) -> Dict[str, Any]:
        """
        Process a single movie and return results
        
        Returns dict with:
        - movie_id: int
        - title: str
        - ratings: dict
        - is_high_rating: bool
        - file_path: str
        - host_path: str
        - tags_modified: bool
        - action_taken: str
        """
        movie = self.client.get_movie(movie_id)
        if not movie:
            return {
                'movie_id': movie_id,
                'error': 'Failed to fetch movie data'
            }
        
        title = movie.get('title', 'Unknown')
        ratings = self.get_movie_ratings(movie)
        is_high = self.is_high_rating(ratings)
        file_path = self.get_movie_file_path(movie)
        
        result = {
            'movie_id': movie_id,
            'title': title,
            'ratings': ratings,
            'is_high_rating': is_high,
            'file_path': file_path,
            'host_path': self.convert_path_to_host(file_path) if file_path else None,
            'tags_modified': False,
            'action_taken': 'none'
        }
        
        if not file_path:
            result['error'] = 'No file path found'
            return result
        
        # Process high-rating movies
        if is_high:
            radarr_settings = self.settings.radarr
            
            # Modify source tag
            movie = self.modify_tags(movie, radarr_settings.action, radarr_settings.source_tag_id)
            
            # Update movie in Radarr
            if self.client.update_movie(movie_id, movie):
                result['tags_modified'] = True
                result['action_taken'] = f"{radarr_settings.action}_tag_{radarr_settings.source_tag_id}"
                
                # Add high-rating tag if we removed the source tag
                if radarr_settings.action == "remove" and radarr_settings.source_tag_id in movie.get('tags', []):
                    if radarr_settings.high_rating_tag_id not in movie.get('tags', []):
                        movie['tags'].append(radarr_settings.high_rating_tag_id)
                        if self.client.update_movie(movie_id, movie):
                            result['action_taken'] += f",add_tag_{radarr_settings.high_rating_tag_id}"
        
        return result


def get_radarr_client() -> RadarrClient:
    """Dependency for FastAPI routes"""
    return RadarrClient()


def get_movie_processor() -> MovieProcessor:
    """Dependency for FastAPI routes"""
    return MovieProcessor()
