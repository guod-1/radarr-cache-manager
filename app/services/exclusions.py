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

    def _apply_path_mappings(self, path: str, source: str = "") -> str:
        """Apply named service path mapping to rewrite path for exclusion file"""
        settings = get_user_settings()
        if source == "radarr":
            m = settings.exclusions.radarr_mapping
        elif source == "sonarr":
            m = settings.exclusions.sonarr_mapping
        elif source == "plexcache":
            m = settings.exclusions.plexcache_mapping
        else:
            # fallback: try all three in order
            for m in [settings.exclusions.radarr_mapping, settings.exclusions.sonarr_mapping, settings.exclusions.plexcache_mapping]:
                if m.from_prefix and path.startswith(m.from_prefix):
                    return m.to_prefix + path[len(m.from_prefix):]
            return path
        if m.from_prefix and path.startswith(m.from_prefix):
            return m.to_prefix + path[len(m.from_prefix):]
        return path

    def _to_container_path(self, path: str) -> str:
        """Translate any path to container-accessible path for existence check"""
        settings = get_user_settings()
        host = settings.exclusions.host_cache_path.rstrip('/')  # /mnt/chloe
        container = settings.exclusions.cache_mount_path.rstrip('/')  # /mnt/cache
        # Already a full host path (e.g. /mnt/chloe/data/...) -> swap prefix
        if path.startswith(host + '/') or path == host:
            return container + path[len(host):]
        # PlexCache raw path (e.g. /chloe/tv/...) -> /mnt/cache/data/media/tv/...
        pc_from = settings.exclusions.plexcache_mapping.from_prefix.rstrip('/')  # /chloe
        pc_to = settings.exclusions.plexcache_mapping.to_prefix  # /mnt/chloe/data/media/
        if pc_from and path.startswith(pc_from + '/'):
            mapped = pc_to.rstrip('/') + '/' + path[len(pc_from):].lstrip('/')
            return container + mapped[len(host):] if mapped.startswith(host) else container + '/' + mapped.lstrip('/')
        # Path already starts with container mount (e.g. /mnt/cache/...) -> use as-is
        if path.startswith(container + '/') or path == container:
            return path
        # Relative path (e.g. /data/media/movies/...) -> /mnt/cache/data/media/movies/
        return container + '/' + path.lstrip('/')

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
        plexcache_paths = set()
        pc_path = Path(settings.exclusions.plexcache_file_path)
        if pc_path.exists():
            try:
                with open(pc_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        plexcache_paths.add(line)
            except Exception as e:
                logger.error(f"Error reading PlexCache file: {e}")
        all_paths.update(plexcache_paths)

        # 3. Radarr - use full file path if downloaded, else folder
        radarr_paths = set()
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
                            radarr_paths.add(path)
            except Exception as e:
                logger.error(f"Radarr exclusion build failed: {e}")

        # 4. Sonarr - individual episode files
        sonarr_paths = set()
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
                                    sonarr_paths.add(ep_path)
                        elif s.get('path'):
                            sonarr_paths.add(s['path'].strip())
            except Exception as e:
                logger.error(f"Sonarr exclusion build failed: {e}")

        all_paths.update(radarr_paths)
        all_paths.update(sonarr_paths)

        # 5. Map paths then validate existence then write.
        # PlexCache raw paths (e.g. /chloe/tv/...) must be mapped to host paths
        # before existence check since raw prefix has no container mount.
        def map_path(p):
            if p in radarr_paths: return self._apply_path_mappings(p, "radarr")
            if p in sonarr_paths: return self._apply_path_mappings(p, "sonarr")
            if p in plexcache_paths: return self._apply_path_mappings(p, "plexcache")
            return self._apply_path_mappings(p)

        valid_paths = []
        skipped = 0
        for p in all_paths:
            # PlexCache paths are already guaranteed on cache - skip existence check
            if p in plexcache_paths:
                valid_paths.append(p)
                continue
            if self._exists_on_cache(p):
                valid_paths.append(p)
            else:
                skipped += 1

        final_list = sorted(valid_paths)
        mapped_paths = [map_path(p) for p in final_list]

        try:
            with open(self.output_file, 'w') as f:
                for path in mapped_paths:
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
