import logging
import os
import datetime
from pathlib import Path
from app.core.config import get_user_settings, save_user_settings
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client

logger = logging.getLogger(__name__)

class ExclusionManager:
    def __init__(self):
        self.output_file = Path("/config/mover_exclusions.txt")

    def _normalize_path(self, path: str) -> str:
        if not path: return ""
        clean = path.strip().strip('"').strip("'")
        settings = get_user_settings()
        
        # Check for movies keyword and replace with user-configured Movie Base Path
        if "/movies/" in clean.lower():
            idx = clean.lower().find("/movies/")
            base = settings.exclusions.movie_base_path.rstrip('/')
            sub_path = clean[idx+8:].lstrip('/')
            return f"{base}/{sub_path}"
            
        # Check for tv keyword and replace with user-configured TV Base Path
        if "/tv/" in clean.lower():
            idx = clean.lower().find("/tv/")
            base = settings.exclusions.tv_base_path.rstrip('/')
            sub_path = clean[idx+4:].lstrip('/')
            return f"{base}/{sub_path}"
            
        return clean

    def build_exclusions(self):
        logger.info("Building exclusions list...")
        all_paths = set()
        settings = get_user_settings()

        # Custom folders
        for folder in settings.exclusions.custom_folders:
            all_paths.add(self._normalize_path(folder))

        # PlexCache-D
        pc_path = Path(settings.exclusions.plexcache_file_path)
        if pc_path.exists():
            with open(pc_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        all_paths.add(self._normalize_path(line))

        # Radarr
        if settings.exclusions.radarr_exclude_tag_ids:
            try:
                movies = get_radarr_client().get_all_movies()
                tag_ids = set(settings.exclusions.radarr_exclude_tag_ids)
                for m in movies:
                    if any(t in tag_ids for t in m.get('tags', [])):
                        path = m.get('path') or (m.get('movieFile', {}).get('path'))
                        if path:
                            all_paths.add(self._normalize_path(path))
            except Exception as e:
                logger.error(f"Radarr exclusion build failed: {e}")

        # Sonarr
        if settings.exclusions.sonarr_exclude_tag_ids:
            try:
                shows = get_sonarr_client().get_all_series()
                tag_ids = set(settings.exclusions.sonarr_exclude_tag_ids)
                for s in shows:
                    if any(t in tag_ids for t in s.get('tags', [])):
                        if s.get('path'):
                            all_paths.add(self._normalize_path(s['path']))
            except Exception as e:
                logger.error(f"Sonarr exclusion build failed: {e}")

        final_list = sorted([p for p in all_paths if p])
        
        with open(self.output_file, 'w') as f:
            for path in final_list:
                f.write(f"{path}\n")
        
        return {"total": len(final_list)}

    def get_exclusion_stats(self):
        if not self.output_file.exists(): return {"total_count": 0}
        with open(self.output_file, 'r') as f:
            return {"total_count": len([l for l in f if l.strip()])}

    def get_all_exclusions(self):
        if not self.output_file.exists(): return []
        with open(self.output_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]

def get_exclusion_manager():
    return ExclusionManager()
