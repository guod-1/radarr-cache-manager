"""
Operations Service
Handles tag operations and exclusion building
"""
import logging
from typing import Dict, Any

from app.core.config import get_user_settings
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.services.exclusions import get_exclusion_manager

logger = logging.getLogger(__name__)


def run_radarr_tag_operation() -> Dict[str, Any]:
    """Run Radarr tag search and replace operation"""
    user_settings = get_user_settings()
    radarr_client = get_radarr_client()
    
    search_tag_id = user_settings.radarr_tag_operation.search_tag_id
    replace_tag_id = user_settings.radarr_tag_operation.replace_tag_id
    
    if not search_tag_id:
        return {"success": False, "message": "No search tag configured"}
    
    try:
        movie_ids = radarr_client.get_movie_ids_by_tag(search_tag_id)
        updated = 0
        
        if replace_tag_id:
            for movie_id in movie_ids:
                movie = radarr_client.get_movie(movie_id)
                if movie:
                    tags = movie.get('tags', [])
                    if search_tag_id in tags:
                        tags.remove(search_tag_id)
                    if replace_tag_id not in tags:
                        tags.append(replace_tag_id)
                    movie['tags'] = tags
                    radarr_client.update_movie(movie_id, movie)
                    updated += 1
        
        return {
            "success": True,
            "movies_found": len(movie_ids),
            "movies_updated": updated
        }
    except Exception as e:
        logger.error(f"Radarr tag operation failed: {e}")
        return {"success": False, "message": str(e)}


def run_sonarr_tag_operation() -> Dict[str, Any]:
    """Run Sonarr tag search and replace operation"""
    user_settings = get_user_settings()
    sonarr_client = get_sonarr_client()
    
    search_tag_id = user_settings.sonarr_tag_operation.search_tag_id
    replace_tag_id = user_settings.sonarr_tag_operation.replace_tag_id
    
    if not search_tag_id:
        return {"success": False, "message": "No search tag configured"}
    
    try:
        series_ids = sonarr_client.get_series_ids_by_tag(search_tag_id)
        updated = 0
        
        if replace_tag_id:
            for series_id in series_ids:
                series = sonarr_client.get_series(series_id)
                if series:
                    tags = series.get('tags', [])
                    if search_tag_id in tags:
                        tags.remove(search_tag_id)
                    if replace_tag_id not in tags:
                        tags.append(replace_tag_id)
                    series['tags'] = tags
                    sonarr_client.update_series(series_id, series)
                    updated += 1
        
        return {
            "success": True,
            "shows_found": len(series_ids),
            "shows_updated": updated
        }
    except Exception as e:
        logger.error(f"Sonarr tag operation failed: {e}")
        return {"success": False, "message": str(e)}


def run_exclusion_builder() -> Dict[str, Any]:
    """Build exclusions from all sources"""
    try:
        exclusion_manager = get_exclusion_manager()
        result = exclusion_manager.combine_exclusions()
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Exclusion builder failed: {e}")
        return {"success": False, "message": str(e)}


def run_full_operation() -> Dict[str, Any]:
    """Run complete operation: Radarr tags + Sonarr tags + build exclusions"""
    logger.info("=== Starting Full Operation ===")
    
    radarr_result = run_radarr_tag_operation()
    sonarr_result = run_sonarr_tag_operation()
    exclusion_result = run_exclusion_builder()
    
    return {
        "radarr": radarr_result,
        "sonarr": sonarr_result,
        "exclusions": exclusion_result
    }
