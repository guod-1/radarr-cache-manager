"""
Configuration Management

Handles all application settings with Pydantic BaseSettings.
Settings are stored in settings.json and can be updated via the web UI.
"""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional, Literal
from pathlib import Path
import json
import os

class AppSettings(BaseSettings):
    """Application settings from environment variables"""
    
    # Directories
    config_dir: Path = Field(default="/config", env="CONFIG_DIR")
    scripts_dir: Path = Field(default="/scripts", env="SCRIPTS_DIR")
    plexcache_dir: Path = Field(default="/plexcache", env="PLEXCACHE_DIR")
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=5858)
    
    # Logging
    log_level: str = Field(default="INFO")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def log_file(self) -> Path:
        """Path to log file"""
        log_dir = self.config_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "radarr-cache-manager.log"
    
    @property
    def settings_file(self) -> Path:
        """Path to settings JSON file"""
        return self.config_dir / "settings.json"
    
    @property
    def exclusions_file(self) -> Path:
        """Path to mover exclusions file"""
        return self.scripts_dir / "mover_exclusions.txt"
    
    @property
    def folder_exclusions_file(self) -> Path:
        """Path to folder exclusions file"""
        return self.scripts_dir / "PlexCache" / "folder_exclusions.txt"
    
    @property
    def plexcache_exclusions_file(self) -> Path:
        """Path to PlexCache-D exclusions file"""
        return self.plexcache_dir / "unraid_mover_exclusions.txt"


class RadarrSettings(BaseModel):
    """Radarr connection settings"""
    url: str = Field(default="http://localhost:7878", description="Radarr URL")
    api_key: str = Field(default="", description="Radarr API key")


class TagOperation(BaseModel):
    """Tag operation configuration"""
    search_tag_id: Optional[int] = Field(default=None, description="Tag ID to search for")
    replace_tag_id: Optional[int] = Field(default=None, description="Tag ID to replace with (optional)")


class ExclusionSettings(BaseModel):
    """Exclusion generation settings"""
    custom_folders: List[str] = Field(default_factory=list, description="Custom folder paths to exclude")
    exclude_tag_ids: List[int] = Field(default_factory=list, description="Tag IDs whose movies should be excluded")
    plexcache_file_path: str = Field(
        default="/plexcache/unraid_mover_exclusions.txt",
        description="Path to PlexCache-D exclusions file"
    )


class SchedulerSettings(BaseModel):
    """Scheduler configuration"""
    enabled: bool = Field(default=False, description="Enable automatic runs")
    cron_expression: str = Field(default="0 */6 * * *", description="Cron expression (every 6 hours)")


class UserSettings(BaseModel):
    """All user-configurable settings"""
    radarr: RadarrSettings = Field(default_factory=RadarrSettings)
    tag_operation: TagOperation = Field(default_factory=TagOperation)
    exclusions: ExclusionSettings = Field(default_factory=ExclusionSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    
    @classmethod
    def load(cls, settings_file: Path) -> "UserSettings":
        """Load settings from JSON file"""
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()
    
    def save(self, settings_file: Path):
        """Save settings to JSON file"""
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)


# Global instances
settings = AppSettings()
user_settings = UserSettings.load(settings.settings_file)


def get_settings() -> AppSettings:
    """Dependency for FastAPI routes"""
    return settings


def get_user_settings() -> UserSettings:
    """Get user settings"""
    return user_settings


def save_user_settings(new_settings: UserSettings):
    """Update and save user settings"""
    global user_settings
    user_settings = new_settings
    user_settings.save(settings.settings_file)
