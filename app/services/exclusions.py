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

    def _normalize_plexcache_path(self, path: str) -> str:
        """Only used for PlexCache paths which may need prefix conversion"""
        if not path: return ""
        clean = path.strip().strip('"').strip("'")
        settings = get_user_settings()

        if "/movies/" in clean.lower():
            idx = clean.lower().find("/movies/")
            base = settings.exclusions.movie_base_path.rstrip('/')
            sub_path = clean[idx+8:].lstrip('/')
            return f"{base}/{sub_path}"

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

        # 1. Custom folders - use as-is
        for folder in settings.exclusions.custom_folders:
            if folder.strip():
                all_paths.add(folder.strip())

        # 2. PlexCache-D paths - these may need path conversion
        pc_path = Path(settings.exclusions.plexcache_file_path)
        if pc_path.exists():
            try:
                with open(pc_path, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            all_paths.add(self._normalize_plexcache_path(line))
            except Exception as e:
                logger.error(f"Error reading PlexCache file: {e}")

        # 3. Radarr paths - use paths directly as Radarr knows the host paths
        if settings.exclusions.radarr_exclude_tag_ids:
            try:
                movies = get_radarr_client().get_all_movies()
                tag_ids = set(settings.exclusions.radarr_exclude_tag_ids)
                for m in movies:
                    if any(t in tag_ids for t in m.get('tags', [])):
                        # Prefer actual file path, fall back to folder
                        file_path = m.get('movieFile', {}).get('path')
                        folder_path = m.get('path')
                        path = file_path or folder_path
                        if path:
                            all_paths.add(path.strip())
            except Exception as e:
                logger.error(f"Radarr exclusion build failed: {e}")

        # 4. Sonarr paths - get individual episode files directly
        if settings.exclusions.sonarr_exclude_tag_ids:
            try:
                sonarr = get_sonarr_client()
                shows = sonarr.get_all_series()
                tag_ids = set(settings.exclusions.sonarr_exclude_tag_ids)
                for s in shows:
                    if any(t in tag_ids for t in s.get('tags', [])):
                        episode_files = sonarr.get_episode_files(s['id'])
                        if episode_files:
                            for ep in episode_files:
                                ep_path = ep.get('path')
                                if ep_path:
                                    all_paths.add(ep_path.strip())
                        elif s.get('path'):
                            all_paths.add(s['path'].strip())
            except Exception as e:
                logger.error(f"Sonarr exclusion build failed: {e}")

        # 5. Validate paths exist on cache
        valid_paths = []
        skipped = 0
        for p in all_paths:
            if os.path.exists(p):
                valid_paths.append(p)
            else:
                skipped += 1

        final_list = sorted(valid_paths)

        try:
            with open(self.output_file, 'w') as f:
                for path in final_list:
                    f.write(f"{path}\n")

            settings.exclusions.last_build = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_user_settings(settings)

            logger.info(f"Exclusions built. Candidates: {len(all_paths)}, On cache: {len(final_list)}, Not on cache (skipped): {skipped}")
            return {"total": len(final_list), "candidates": len(all_paths), "skipped": skipped}

        except Exception as e:
            logger.error(f"Failed to write exclusion file: {e}")
            raise e

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
