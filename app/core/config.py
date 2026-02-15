import json
import logging
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)
CONFIG_FILE = Path("/config/config.json")

class RadarrSettings(BaseModel):
    url: str = "http://localhost:7878"
    api_key: str = ""

class SonarrSettings(BaseModel):
    url: str = "http://localhost:8989"
    api_key: str = ""

class RadarrTagOperation(BaseModel):
    search_tag_id: Optional[int] = None
    replace_tag_id: Optional[int] = None

class SonarrTagOperation(BaseModel):
    search_tag_id: Optional[int] = None
    replace_tag_id: Optional[int] = None

class ExclusionSettings(BaseModel):
    custom_folders: List[str] = []
    plexcache_file_path: str = "/mnt/user/appdata/plexcache/plexcache"
    exclude_tag_ids: List[int] = []

class SchedulerSettings(BaseModel):
    enabled: bool = False
    cron_expression: str = "0 */6 * * *"
    ca_mover_check_cron: str = "30 23 * * *"

class LastRunSettings(BaseModel):
    radarr: str = "Never"
    sonarr: str = "Never"
    exclusion: str = "Never"
    mover_check: str = "Never"

class UserSettings(BaseModel):
    radarr: RadarrSettings = RadarrSettings()
    sonarr: SonarrSettings = SonarrSettings()
    radarr_tag_operation: RadarrTagOperation = RadarrTagOperation()
    sonarr_tag_operation: SonarrTagOperation = SonarrTagOperation()
    exclusions: ExclusionSettings = ExclusionSettings()
    scheduler: SchedulerSettings = SchedulerSettings()
    last_run: LastRunSettings = LastRunSettings()

def get_user_settings() -> UserSettings:
    if not CONFIG_FILE.exists():
        return UserSettings()
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return UserSettings(**data)
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        return UserSettings()

def save_user_settings(settings: UserSettings):
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(settings.json(indent=4))
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
