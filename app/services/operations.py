"""
Operations Service

Orchestrates two main workflows:
1. Tag Operations: Find movies with specific tags and optionally replace tags
2. Exclusion Building: Combine multiple sources into mover_exclusions.txt
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

from app.services.radarr import get_radarr_client
from app.services.exclusions import ExclusionManager
from app.core.config import get_user_settings

logger = logging.getLogger(__name__)


class OperationResult:
    """Result of a cache manager operation"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = None
        self.success = False
        self.error = None
        self.movies_processed = 0
        self.tags_modified_count = 0
        self.exclusions_generated = 0
        self.operation_type = None
    
    def finish(self, success: bool = True, error: str = None):
        """Mark operation as finished"""
        self.end_time = datetime.now()
        self.success = success
        self.error = error
    
    @property
    def duration(self) -> float:
        """Duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'success': self.success,
            'error': self.error,
            'operation_type': self.operation_type,
            'movies_processed': self.movies_processed,
            'tags_modified_count': self.tags_modified_count,
            'exclusions_generated': self.exclusions_generated
        }


def run_tag_operation() -> Dict[str, Any]:
    """
    Run tag replacement operation
    
    Finds movies with search_tag_id and optionally replaces with replace_tag_id
    """
    result = OperationResult()
    result.operation_type = "tag_operation"
    
    try:
        logger.info("=== Starting Tag Operation ===")
        
        radarr_client = get_radarr_client()
        settings = get_user_settings()
        
        # Check if tag operation is configured
        if not settings.tag_operation.search_tag_id:
            logger.warning("No search tag ID configured")
            result.finish(success=True)
            return result.to_dict()
        
        # Test Radarr connection
        logger.info("Testing Radarr connection...")
        if not radarr_client.test_connection():
            raise Exception("Failed to connect to Radarr. Check settings.")
        
        # Fetch movies with search tag
        search_tag = settings.tag_operation.search_tag_id
        logger.info(f"Fetching movies with tag ID: {search_tag}")
        movie_ids = radarr_client.get_movie_ids_by_tag(search_tag)
        
        if not movie_ids:
            logger.info("No movies found with the specified tag")
            result.finish(success=True)
            return result.to_dict()
        
        logger.info(f"Found {len(movie_ids)} movies")
        
        # Process each movie (replace tag if configured)
        replace_tag = settings.tag_operation.replace_tag_id
        if replace_tag:
            logger.info(f"Replacing tag {search_tag} with tag {replace_tag}")
            
            for movie_id in movie_ids:
                try:
                    movie = radarr_client.get_movie(movie_id)
                    if not movie:
                        continue
                    
                    title = movie.get('title', 'Unknown')
                    tags = movie.get('tags', [])
                    
                    # Replace tag
                    if search_tag in tags:
                        tags.remove(search_tag)
                    if replace_tag not in tags:
                        tags.append(replace_tag)
                    
                    movie['tags'] = tags
                    
                    # Update movie
                    if radarr_client.update_movie(movie_id, movie):
                        result.tags_modified_count += 1
                        logger.info(f"Updated tags for: {title}")
                    
                    result.movies_processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing movie {movie_id}: {e}")
                    continue
        else:
            logger.info("No replacement tag configured, skipping tag modification")
            result.movies_processed = len(movie_ids)
        
        logger.info(f"Tag operation complete: {result.tags_modified_count} movies updated")
        result.finish(success=True)
        
    except Exception as e:
        logger.error(f"Tag operation failed: {e}")
        result.finish(success=False, error=str(e))
    
    return result.to_dict()


def run_exclusion_builder() -> Dict[str, Any]:
    """
    Build mover_exclusions.txt from multiple sources:
    1. Custom folders
    2. Movies with specific tags
    3. PlexCache-D exclusions
    """
    result = OperationResult()
    result.operation_type = "exclusion_builder"
    
    try:
        logger.info("=== Starting Exclusion Builder ===")
        
        radarr_client = get_radarr_client()
        exclusion_manager = ExclusionManager()
        settings = get_user_settings()
        
        # Clear temporary exclusions
        exclusion_manager.clear_temp_exclusions()
        
        # Step 1: Add custom folders
        logger.info("Adding custom folder exclusions...")
        for folder in settings.exclusions.custom_folders:
            exclusion_manager.add_exclusion(folder)
            logger.info(f"Added folder: {folder}")
        
        # Step 2: Add movies with specific tags
        if settings.exclusions.exclude_tag_ids:
            logger.info(f"Adding movies with tags: {settings.exclusions.exclude_tag_ids}")
            
            if radarr_client.test_connection():
                for tag_id in settings.exclusions.exclude_tag_ids:
                    movie_ids = radarr_client.get_movie_ids_by_tag(tag_id)
                    logger.info(f"Found {len(movie_ids)} movies with tag {tag_id}")
                    
                    for movie_id in movie_ids:
                        try:
                            movie = radarr_client.get_movie(movie_id)
                            if movie:
                                file_path = movie.get('movieFile', {}).get('path')
                                if file_path:
                                    # Convert Plex path to host path
                                    host_path = file_path.replace('/data/media/movies/', '/mnt/chloe/data/media/movies/')
                                    exclusion_manager.add_exclusion(host_path)
                                    result.movies_processed += 1
                        except Exception as e:
                            logger.error(f"Error processing movie {movie_id}: {e}")
                            continue
        
        # Step 3: Combine all sources
        logger.info("Combining all exclusion sources...")
        exclusion_count = exclusion_manager.combine_exclusions()
        result.exclusions_generated = exclusion_count
        
        logger.info(f"=== Exclusion Builder Complete ===")
        logger.info(f"Movies processed: {result.movies_processed}")
        logger.info(f"Total exclusions: {result.exclusions_generated}")
        
        result.finish(success=True)
        
    except Exception as e:
        logger.error(f"Exclusion builder failed: {e}")
        result.finish(success=False, error=str(e))
    
    return result.to_dict()


def run_full_operation() -> Dict[str, Any]:
    """
    Run both operations:
    1. Tag operation (if configured)
    2. Exclusion builder
    """
    logger.info("=== Running Full Operation ===")
    
    results = {
        'tag_operation': None,
        'exclusion_builder': None
    }
    
    # Run tag operation
    settings = get_user_settings()
    if settings.tag_operation.search_tag_id:
        logger.info("Running tag operation...")
        results['tag_operation'] = run_tag_operation()
    else:
        logger.info("Skipping tag operation (not configured)")
    
    # Run exclusion builder
    logger.info("Running exclusion builder...")
    results['exclusion_builder'] = run_exclusion_builder()
    
    logger.info("=== Full Operation Complete ===")
    
    return results
