import logging
from pathlib import Path
from typing import List, Set
from app.core.config import get_user_settings
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client

logger = logging.getLogger(__name__)

class ExclusionManager:
    def __init__(self):
        self.settings = get_user_settings()
        self.output_file = Path("/config/mover_exclusions.txt")

    def _normalize_path(self, path: str) -> str:
        """
        Forces paths to match the specific /mnt/chloe/data/media structure.
        """
        if not path:
            return ""
            
        clean_path = path.strip()
        
        # Mapping logic for Radarr/Sonarr and PlexCache lines
        if "/movies/" in clean_path:
            try:
                relative_part = clean_path.split("/movies/", 1)[1]
                return f"/mnt/chloe/data/media/movies/{relative_part}"
            except IndexError: pass

        if "/tv/" in clean_path:
            try:
                relative_part = clean_path.split("/tv/", 1)[1]
                return f"/mnt/chloe/data/media/tv/{relative_part}"
            except IndexError: pass
        
        return clean_path

    def combine_exclusions(self) -> int:
        all_paths = set()

        # A. Manual Folder Exclusions
        if self.settings.exclusions.custom_folders:
            for folder in self.settings.exclusions.custom_folders:
                all_paths.add(self._normalize_path(folder))

        # B. PlexCache-D Exclusions (Crucial Fix)
        plex_cache_file = Path(self.settings.exclusions.plexcache_file_path)
        if plex_cache_file.exists():
            try:
                with open(plex_cache_file, 'r') as f:
                    for line in f:
                        clean = line.strip()
                        # Skip empty lines and comments
                        if not clean or clean.startswith('#'):
                            continue
                        # Normalize these paths too!
                        all_paths.add(self._normalize_path(clean))
                logger.info(f"Loaded and normalized exclusions from {plex_cache_file}")
            except Exception as e:
                logger.error(f"Error reading PlexCache file: {e}")

        # C. Tags (Radarr/Sonarr)
        target_tags = set(self.settings.exclusions.exclude_tag_ids)
        if target_tags:
            # Add Radarr files
            try:
                radarr = get_radarr_client()
                movies = radarr.get_all_movies()
                for m in movies:
                    if m.get('hasFile') and any(t in target_tags for t in m.get('tags', [])):
                        movie_file = m.get('movieFile')
                        if movie_file:
                            all_paths.add(self._normalize_path(movie_file['path']))
            except Exception as e: logger.error(f"Radarr fetch failed: {e}")

            # Add Sonarr files
            try:
                sonarr = get_sonarr_client()
                shows = sonarr.get_all_shows()
                for s in shows:
                    if any(t in target_tags for t in s.get('tags', [])):
                        ep_files = sonarr.get_episode_files(s['id'])
                        for ep in ep_files:
                            all_paths.add(self._normalize_path(ep['path']))
            except Exception as e: logger.error(f"Sonarr fetch failed: {e}")

        # Write to final file
        try:
            with open(self.output_file, 'w') as f:
                for path in sorted(list(all_paths)):
                    f.write(f"{path}\n")
            logger.info(f"Wrote {len(all_paths)} total paths to {self.output_file}")
        except Exception as e:
            logger.error(f"Failed to write exclusion file: {e}")

        return len(all_paths)

    def get_exclusion_stats(self) -> dict:
        if not self.output_file.exists():
            return {"total_count": 0}
        try:
            with open(self.output_file, 'r') as f:
                return {"total_count": len([l for l in f if l.strip()])}
        except:
            return {"total_count": 0}

def get_exclusion_manager():
    return ExclusionManager()
