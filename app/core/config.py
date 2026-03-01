import json
import os
import shutil
import logging
from pydantic import BaseModel
from typing import List, Optional

logger = logging.getLogger(__name__)

CONFIG_PATH = "/config/settings.json"
BACKUP_PATH = "/config/settings.json.bak"


class RadarrSettings(BaseModel):
    url: str = ""
    api_key: str = ""


class SonarrSettings(BaseModel):
    url: str = ""
    api_key: str = ""


class SchedulerSettings(BaseModel):
    enabled: bool = True
    cron_expression: str = "0 */6 * * *"


class ServicePathMapping(BaseModel):
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
    radarr_mapping: ServicePathMapping = ServicePathMapping(from_prefix="/data/", to_prefix="/mnt/chloe/data/")
    sonarr_mapping: ServicePathMapping = ServicePathMapping(from_prefix="/data/", to_prefix="/mnt/chloe/data/")
    plexcache_mapping: ServicePathMapping = ServicePathMapping(from_prefix="/chloe/", to_prefix="/mnt/chloe/data/media/")
    last_build: Optional[str] = None
    full_sync_cron: str = "0 * * * *"
    log_monitor_cron: str = "*/5 * * * *"
    last_stats_update: Optional[str] = None


class UserSettings(BaseModel):
    radarr: RadarrSettings = RadarrSettings()
    sonarr: SonarrSettings = SonarrSettings()
    exclusions: ExclusionSettings = ExclusionSettings()
    scheduler: SchedulerSettings = SchedulerSettings()


def _log_settings_snapshot(settings: UserSettings, context: str):
    """Log a non-sensitive snapshot of key settings for debugging."""
    logger.debug(
        f"[CONFIG:{context}] "
        f"radarr_url={settings.radarr.url!r} "
        f"radarr_key={'SET' if settings.radarr.api_key else 'EMPTY'} "
        f"sonarr_url={settings.sonarr.url!r} "
        f"sonarr_key={'SET' if settings.sonarr.api_key else 'EMPTY'} "
        f"radarr_tags={settings.exclusions.radarr_exclude_tag_ids} "
        f"sonarr_tags={settings.exclusions.sonarr_exclude_tag_ids} "
        f"full_sync_cron={settings.exclusions.full_sync_cron!r} "
        f"log_monitor_cron={settings.exclusions.log_monitor_cron!r}"
    )


def _try_load_json(path: str) -> Optional[dict]:
    """Attempt to read and parse a JSON file. Returns None on any failure."""
    try:
        with open(path, "r") as f:
            raw = f.read()
        if not raw.strip():
            logger.warning(f"[CONFIG] File is empty: {path}")
            return None
        data = json.loads(raw)
        logger.debug(f"[CONFIG] Successfully parsed JSON from {path} ({len(raw)} bytes)")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"[CONFIG] JSON parse error in {path}: {e}")
        return None
    except OSError as e:
        logger.error(f"[CONFIG] OS error reading {path}: {e}")
        return None


def get_user_settings() -> UserSettings:
    logger.debug(f"[CONFIG] get_user_settings() called")

    # --- Primary config ---
    if os.path.exists(CONFIG_PATH):
        file_size = os.path.getsize(CONFIG_PATH)
        logger.debug(f"[CONFIG] Primary config found: {CONFIG_PATH} ({file_size} bytes)")

        data = _try_load_json(CONFIG_PATH)
        if data is not None:
            try:
                settings = UserSettings.model_validate(data)
                _log_settings_snapshot(settings, "LOADED")
                return settings
            except Exception as e:
                logger.error(f"[CONFIG] Pydantic validation failed for {CONFIG_PATH}: {e}")
        else:
            logger.error(f"[CONFIG] Primary config unreadable — attempting backup recovery")
    else:
        logger.info(f"[CONFIG] No config file at {CONFIG_PATH} — will use defaults")

    # --- Backup recovery ---
    if os.path.exists(BACKUP_PATH):
        backup_size = os.path.getsize(BACKUP_PATH)
        logger.warning(f"[CONFIG] Trying backup: {BACKUP_PATH} ({backup_size} bytes)")
        data = _try_load_json(BACKUP_PATH)
        if data is not None:
            try:
                settings = UserSettings.model_validate(data)
                logger.warning(f"[CONFIG] Recovered settings from backup — restoring primary")
                _log_settings_snapshot(settings, "RECOVERED")
                save_user_settings(settings)
                return settings
            except Exception as e:
                logger.error(f"[CONFIG] Backup validation also failed: {e}")

    # --- Last resort: defaults ---
    logger.error(
        f"[CONFIG] *** Both primary and backup configs failed — returning DEFAULTS. "
        f"Radarr/Sonarr URLs will be EMPTY. Check /config/ for corruption. ***"
    )
    return UserSettings()


def save_user_settings(settings: UserSettings):
    _log_settings_snapshot(settings, "SAVING")

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    tmp_path = CONFIG_PATH + ".tmp"

    try:
        payload = json.dumps(settings.model_dump(), indent=4)
        logger.debug(f"[CONFIG] Writing {len(payload)} bytes to {tmp_path}")

        with open(tmp_path, "w") as f:
            f.write(payload)

        # Verify the temp file is valid before replacing the real one
        verify_data = _try_load_json(tmp_path)
        if verify_data is None:
            raise ValueError("Temp file failed post-write verification — aborting save")

        # Back up the current good config
        if os.path.exists(CONFIG_PATH) and os.path.getsize(CONFIG_PATH) > 0:
            shutil.copy2(CONFIG_PATH, BACKUP_PATH)
            logger.debug(f"[CONFIG] Backed up existing config to {BACKUP_PATH}")

        # Atomic replace
        os.replace(tmp_path, CONFIG_PATH)
        logger.debug(f"[CONFIG] Atomic replace complete -> {CONFIG_PATH}")

    except Exception as e:
        logger.error(f"[CONFIG] save_user_settings FAILED: {e}")
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise
