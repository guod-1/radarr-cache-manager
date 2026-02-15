import logging
from datetime import datetime
from app.services.exclusions import get_exclusion_manager
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.core.config import get_user_settings, save_user_settings

logger = logging.getLogger(__name__)

def _update_timestamp(field: str):
    settings = get_user_settings()
    setattr(settings.last_run, field, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    save_user_settings(settings)

async def run_exclusion_builder():
    try:
        manager = get_exclusion_manager()
        count = manager.combine_exclusions()
        _update_timestamp("exclusion")
        return {"status": "success", "message": f"Built {count} exclusions"}
    except Exception as e:
        logger.error(f"Exclusion builder failed: {e}")
        return {"status": "error", "message": str(e)}

async def run_full_sync():
    # 1. Run Radarr Ops
    _update_timestamp("radarr")
    # 2. Run Sonarr Ops
    _update_timestamp("sonarr")
    # 3. Build File
    return await run_exclusion_builder()
