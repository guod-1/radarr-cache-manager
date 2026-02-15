import json
import os
from pydantic import BaseModel
from typing import List, Optional

CONFIG_PATH = "/config/settings.json"

class RadarrTagOperation(BaseModel):
    tag_id: int
    action: str

class SonarrTagOperation(BaseModel):
    tag_id: int
    action: str

class SchedulerSettings(BaseModel):
    enabled: bool = True
    cron_expression: str = "0 */6 * * *"

class ExclusionSettings(BaseModel):
    custom_folders: List[str] = []
    exclude_tag_ids: List[int] = []
    plexcache_file_path: str = "/plexcache/unraid_mover_exclusions.txt"
    last_build: Optional[str] = ""

class RadarrSettings(BaseModel):
    url: str = ""
    api_key: str = ""
    last_sync: Optional[str] = ""

class SonarrSettings(BaseModel):
    url: str = ""
    api_key: str = ""
    last_sync: Optional[str] = ""

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
        except:
            return UserSettings()
    return UserSettings()

def save_user_settings(settings: UserSettings):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(settings.dict(), f, indent=4)
