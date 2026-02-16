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
        
        # Use configurable base paths from settings
        if "/movies/" in clean.lower():
            idx = clean.lower().find("/movies/")
            return f"{settings.exclusions.movie_base_path.rstrip('/')}/{clean[idx+8:].lstrip('/')}"
        if "/tv/" in clean.lower():
            idx = clean.lower().find("/tv/")
            return f"{settings.exclusions.tv_base_path.rstrip('/')}/{clean[idx+4:].lstrip('/')}"
        return clean

    def combine_exclusions(self) -> int:
        logger.info("!!! STARTING EXCLUSION COMBINATION PROCESS !!!")
        all_paths = set()
        settings = get_user_settings()

        for folder in settings.exclusions.custom_folders:
            all_paths.add(self._normalize_path(folder))

        pc_path = Path(settings.exclusions.plexcache_file_path)
        if pc_path.exists():
            with open(pc_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        all_paths.add(self._normalize_path(line))
            logger.info(f"Integrated lines from {pc_path}")

        radarr_tags = set(settings.exclusions.radarr_exclude_tag_ids)
        if radarr_tags:
            try:
                movies = get_radarr_client().get_all_movies()
                for m in movies:
                    if m.get('hasFile') and any(t in radarr_tags for t in m.get('tags', [])):
                        all_paths.add(self._normalize_path(m['movieFile']['path']))
            except Exception as e:
                logger.error(f"Error processing Radarr tags: {e}")

        sonarr_tags = set(settings.exclusions.sonarr_exclude_tag_ids)
        if sonarr_tags:
            try:
                shows = get_sonarr_client().get_all_series()
                for s in shows:
                    if any(t in sonarr_tags for t in s.get('tags', [])):
                        all_paths.add(self._normalize_path(s['path']))
            except Exception as e:
                logger.error(f"Error processing Sonarr tags: {e}")

        final_list = sorted([p for p in all_paths if p])
        os.makedirs(self.output_file.parent, exist_ok=True)
        with open(self.output_file, 'w') as f:
            for path in final_list:
                f.write(f"{path}\n")
        
        settings.exclusions.last_build = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_user_settings(settings)
        
        logger.info(f"!!! COMPLETED !!! Total items: {len(final_list)}")
        return len(final_list)

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
