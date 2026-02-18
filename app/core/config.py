import json
import os
from pydantic import BaseModel
from typing import List, Optional
from __future__ import annotations

CONFIG_PATH = "/config/settings.json"

class RadarrSettings(BaseModel):
    url: str = ""
    api_key: str = ""

class SonarrSettings(BaseModel):
    url: str = ""
    api_key: str = ""

class SchedulerSettings(BaseModel):
    enabled: bool = True
    cron_expression: str = "0 */6 * * *"

class PathMapping(BaseModel):
    from_prefix: str = ""
    to_prefix: str = ""

class ExclusionSettings(BaseModel):
    custom_folders: List[str] = []
    radarr_exclude_tag_ids: List[int] = []
    sonarr_exclude_tag_ids: List[int] = []
    plexcache_file_path: str = "/plexcache/unraid_mover_exclusions.txt"
    ca_mover_log_path: str = "/mover_logs/ca.mover.tuning.log"
    cache_mount_path: str = "/mnt/cache"
    host_cache_path: str = "/mnt/chloe"
    movie_base_path: str = "/mnt/cache/data/media/movies/"
    tv_base_path: str = "/mnt/cache/data/media/tv/"
    path_mappings: List[PathMapping] = [
        PathMapping(from_prefix="/data/", to_prefix="/mnt/chloe/data/"),
        PathMapping(from_prefix="/chloe/", to_prefix="/mnt/chloe/data/media/")
    ]
    last_build: Optional[str] = None
    full_sync_cron: str = "0 * * * *"
    log_monitor_cron: str = "*/5 * * * *"
    last_stats_update: Optional[str] = None

class UserSettings(BaseModel):
    radarr: RadarrSettings = RadarrSettings()
    sonarr: SonarrSettings = SonarrSettings()
    exclusions: ExclusionSettings = ExclusionSettings()
    scheduler: SchedulerSettings = SchedulerSettings()

def get_user_settings() -> UserSettings:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return UserSettings.parse_obj(json.load(f))
        except: return UserSettings()
    return UserSettings()

def save_user_settings(settings: UserSettings):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(settings.dict(), f, indent=4)
