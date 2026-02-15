import logging
from pathlib import Path
from typing import List
from app.core.config import get_user_settings
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client

logger = logging.getLogger(__name__)

class ExclusionManager:
    def __init__(self):
        self.settings = get_user_settings()
        self.output_file = Path("/config/mover_exclusions.txt")

    def combine_exclusions(self) -> int:
        """Fresh build of the exclusion file from all sources"""
        all_paths = set()

        # A. Add Manual Folder Exclusions from Settings
        if self.settings.exclusion_settings.folders:
            for folder in self.settings.exclusion_settings.folders:
                all_paths.add(folder.strip())

        # B. Add PlexCache-D Exclusions
        plex_cache_file = Path(self.settings.exclusion_settings.plexcache_file)
        if plex_cache_file.exists():
            with open(plex_cache_file, 'r') as f:
                for line in f:
                    clean = line.strip()
                    if clean: all_paths.add(clean)

        # C. Add Tagged Movies (Radarr)
        if self.settings.radarr_tag_operation.search_tag_id:
            try:
                radarr = get_radarr_client()
                movies = radarr.get_all_movies()
                for m in movies:
                    if self.settings.radarr_tag_operation.search_tag_id in m.get('tags', []):
                        all_paths.add(m.get('path'))
            except Exception as e:
                logger.error(f"Radarr exclusion fetch failed: {e}")

        # D. Add Tagged Shows (Sonarr)
        if self.settings.sonarr_tag_operation.search_tag_id:
            try:
                sonarr = get_sonarr_client()
                shows = sonarr.get_all_shows()
                for s in shows:
                    if self.settings.sonarr_tag_operation.search_tag_id in s.get('tags', []):
                        all_paths.add(s.get('path'))
            except Exception as e:
                logger.error(f"Sonarr exclusion fetch failed: {e}")

        # Write fresh file
        with open(self.output_file, 'w') as f:
            for path in sorted(list(all_paths)):
                f.write(f"{path}\n")

        return len(all_paths)

    def get_exclusion_stats(self) -> dict:
        """Returns stats about the current exclusion file"""
        if not self.output_file.exists():
            return {"total_count": 0, "file_size": 0}
        
        try:
            with open(self.output_file, 'r') as f:
                lines = [l.strip() for l in f if l.strip()]
            return {
                "total_count": len(lines),
                "file_size": self.output_file.stat().st_size
            }
        except Exception as e:
            logger.error(f"Error reading stats: {e}")
            return {"total_count": 0, "file_size": 0}

def get_exclusion_manager():
    return ExclusionManager()
