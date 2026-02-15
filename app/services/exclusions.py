import logging
from pathlib import Path
from app.core.config import get_user_settings
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client

logger = logging.getLogger(__name__)

class ExclusionManager:
    def __init__(self):
        self.settings = get_user_settings()
        self.output_file = Path("/config/mover_exclusions.txt")

    def _normalize_path(self, path: str) -> str:
        if not path: return ""
        clean = path.strip().strip('"').strip("'")
        
        # Mapping logic to force /mnt/chloe structure
        if "/movies/" in clean.lower():
            idx = clean.lower().find("/movies/")
            return f"/mnt/chloe/data/media/movies/{clean[idx+8:]}"
        if "/tv/" in clean.lower():
            idx = clean.lower().find("/tv/")
            return f"/mnt/chloe/data/media/tv/{clean[idx+4:]}"
        return clean

    def combine_exclusions(self) -> int:
        all_paths = set()

        # A. PlexCache File
        pc_path = Path(self.settings.exclusions.plexcache_file_path)
        if pc_path.exists():
            try:
                with open(pc_path, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            all_paths.add(self._normalize_path(line))
            except Exception as e: logger.error(f"PlexCache read error: {e}")

        # B. Tags
        target_tags = set(self.settings.exclusions.exclude_tag_ids)
        if target_tags:
            try:
                movies = get_radarr_client().get_all_movies()
                for m in movies:
                    if m.get('hasFile') and any(t in target_tags for t in m.get('tags', [])):
                        all_paths.add(self._normalize_path(m['movieFile']['path']))
            except Exception: pass

        # Write file
        final_list = sorted([p for p in all_paths if p])
        with open(self.output_file, 'w') as f:
            for path in final_list: f.write(f"{path}\n")
        return len(final_list)

    def get_exclusion_stats(self) -> dict:
        if not self.output_file.exists(): return {"total_count": 0}
        with open(self.output_file, 'r') as f:
            return {"total_count": len([l for l in f if l.strip()])}

def get_exclusion_manager():
    return ExclusionManager()
