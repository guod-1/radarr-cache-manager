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

    def _to_container_path(self, path: str) -> str:
        """Prepend container cache mount to get checkable path"""
        settings = get_user_settings()
        return settings.exclusions.cache_mount_path.rstrip('/') + '/' + path.lstrip('/')

    def _to_host_path(self, path: str) -> str:
        """Prepend host cache path for writing to exclusion file"""
        settings = get_user_settings()
        return settings.exclusions.host_cache_path.rstrip('/') + '/' + path.lstrip('/')

    def _exists_on_cache(self, path: str) -> bool:
        """Check if path exists via container mount"""
        container_path = self._to_container_path(path)
        result = os.path.exists(container_path)
        logger.debug(f"PATH CHECK | container={container_path!r} exists={result}")
        return result

    def build_exclusions(self):
        logger.info("Building exclusions list...")
        settings = get_user_settings()
        all_paths = set()

        # 1. Custom folders - use as-is
        for folder in settings.exclusions.custom_folders:
            if folder.strip():
                all_paths.add(folder.strip())

        # 2. PlexCache-D paths
        pc_path = Path(settings.exclusions.plexcache_file_path)
        if pc_path.exists():
            try:
                with open(pc_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            all_paths.add(line)
            except Exception as e:
                logger.error(f"Error reading PlexCache file: {e}")

        # 3. Radarr - use full file path if downloaded, else folder
        if settings.exclusions.radarr_exclude_tag_ids:
            try:
                movies = get_radarr_client().get_all_movies()
                tag_ids = set(settings.exclusions.radarr_exclude_tag_ids)
                for m in movies:
                    if any(t in tag_ids for t in m.get('tags', [])):
                        file_path = m.get('movieFile', {}).get('path')
                        folder_path = m.get('path')
                        path = (file_path or folder_path or '').strip()
                        if path:
                            all_paths.add(path)
            except Exception as e:
                logger.error(f"Radarr exclusion build failed: {e}")

        # 4. Sonarr - individual episode files
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
                                ep_path = (ep.get('path') or '').strip()
                                if ep_path:
                                    all_paths.add(ep_path)
                        elif s.get('path'):
                            all_paths.add(s['path'].strip())
            except Exception as e:
                logger.error(f"Sonarr exclusion build failed: {e}")

        # 5. Validate existence via container path, write host path to file
        valid_paths = []
        skipped = 0
        for p in all_paths:
            if self._exists_on_cache(p):
                valid_paths.append(p)
            else:
                skipped += 1

        final_list = sorted(valid_paths)

        # Convert validated paths to host paths for the exclusion file
        host_paths = []
        settings2 = get_user_settings()
        for p in final_list:
            # PlexCache paths already have full host path, others need prefix
            if p.startswith(settings2.exclusions.host_cache_path) or p.startswith(settings2.exclusions.cache_mount_path):
                host_paths.append(p)
            else:
                host_paths.append(self._to_host_path(p))

        try:
            with open(self.output_file, 'w') as f:
                for path in host_paths:
                    f.write(f"{path}\n")

            settings.exclusions.last_build = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_user_settings(settings)

            logger.info(f"Exclusions built. Candidates: {len(all_paths)}, On cache: {len(final_list)}, Skipped: {skipped}")
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
