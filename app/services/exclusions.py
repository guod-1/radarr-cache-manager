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
        Maps container paths to Unraid host paths.
        Example: /chloe/tv/... -> /mnt/user/chloe/tv/...
        """
        if not path:
            return ""
            
        clean_path = path.strip()
        
        # 1. Custom Mapping for 'chloe' share
        if clean_path.startswith("/chloe"):
            return clean_path.replace("/chloe", "/mnt/user/chloe", 1)
            
        # 2. Common Unraid mapping (just in case)
        if clean_path.startswith("/media"):
            return clean_path.replace("/media", "/mnt/user/media", 1)
            
        return clean_path

    def combine_exclusions(self) -> int:
        """Fresh build of the exclusion file from all sources"""
        all_paths = set()

        # ---------------------------------------------------------
        # A. Manual Folder Exclusions
        # ---------------------------------------------------------
        if self.settings.exclusions.custom_folders:
            for folder in self.settings.exclusions.custom_folders:
                all_paths.add(self._normalize_path(folder))

        # ---------------------------------------------------------
        # B. PlexCache-D Exclusions
        # ---------------------------------------------------------
        plex_cache_file = Path(self.settings.exclusions.plexcache_file_path)
        if plex_cache_file.exists():
            try:
                with open(plex_cache_file, 'r') as f:
                    for line in f:
                        clean = line.strip()
                        # Skip empty lines and comments
                        if not clean or clean.startswith('#'):
                            continue
                        all_paths.add(self._normalize_path(clean))
            except Exception as e:
                logger.error(f"Error reading PlexCache file: {e}")

        # ---------------------------------------------------------
        # C. Exclude Movies by Tag (Radarr)
        # ---------------------------------------------------------
        # 1. Gather all tags we want to exclude (Set logic for speed)
        target_tags = set(self.settings.exclusions.exclude_tag_ids)
        
        # 2. Also include the 'Search Tag' from the Operations tab if set
        if self.settings.radarr_tag_operation.search_tag_id:
            target_tags.add(self.settings.radarr_tag_operation.search_tag_id)

        if target_tags:
            try:
                radarr = get_radarr_client()
                movies = radarr.get_all_movies()
                count = 0
                for m in movies:
                    # Check if movie has ANY of our target tags
                    m_tags = m.get('tags', [])
                    if any(t in target_tags for t in m_tags):
                        path = m.get('path')
                        if path:
                            all_paths.add(self._normalize_path(path))
                            count += 1
                logger.info(f"Found {count} movies matching exclusion tags: {target_tags}")
            except Exception as e:
                logger.error(f"Radarr exclusion fetch failed: {e}")

        # ---------------------------------------------------------
        # D. Exclude Shows by Tag (Sonarr)
        # ---------------------------------------------------------
        # Assuming the same tag IDs might apply, or we check if user wants this feature later.
        # For now, we reuse the same list but check Sonarr connections.
        if target_tags:
            try:
                sonarr = get_sonarr_client()
                shows = sonarr.get_all_shows()
                count = 0
                for s in shows:
                    s_tags = s.get('tags', [])
                    if any(t in target_tags for t in s_tags):
                        path = s.get('path')
                        if path:
                            all_paths.add(self._normalize_path(path))
                            count += 1
                logger.info(f"Found {count} shows matching exclusion tags")
            except Exception as e:
                # Silent fail if Sonarr isn't configured, that's fine
                pass

        # ---------------------------------------------------------
        # Write fresh file
        # ---------------------------------------------------------
        try:
            with open(self.output_file, 'w') as f:
                for path in sorted(list(all_paths)):
                    f.write(f"{path}\n")
            logger.info(f"Wrote {len(all_paths)} paths to {self.output_file}")
        except Exception as e:
            logger.error(f"Failed to write exclusion file: {e}")

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
