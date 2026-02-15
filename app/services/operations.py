import datetime
import logging
from app.core.config import get_user_settings, save_user_settings
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.services.exclusions import get_exclusion_manager

logger = logging.getLogger(__name__)


async def run_exclusion_builder():
    """Run only the exclusion builder"""
    logger.info("Running exclusion builder...")
    settings = get_user_settings()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    try:
        excl = get_exclusion_manager()
        count = excl.combine_exclusions()
        settings.exclusions.last_build = now
        save_user_settings(settings)
        
        logger.info(f"Exclusion list rebuilt with {count} items.")
        return {
            "status": "success",
            "message": f"Built {count} exclusions successfully"
        }
    except Exception as e:
        logger.error(f"Exclusion builder failed: {e}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }


async def run_full_sync():
    """Run full sync: Radarr + Sonarr + Exclusions"""
    logger.info("Starting system-wide sync and build...")
    settings = get_user_settings()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Update Sync Times
    try:
        get_radarr_client().get_all_tags()
        settings.radarr.last_sync = now
    except Exception as e:
        logger.error(f"Radarr sync failed: {e}")
    
    try:
        get_sonarr_client().get_all_tags()
        settings.sonarr.last_sync = now
    except Exception as e:
        logger.error(f"Sonarr sync failed: {e}")
    
    # Run Exclusion Builder
    try:
        excl = get_exclusion_manager()
        count = excl.combine_exclusions()
        settings.exclusions.last_build = now
        logger.info(f"Exclusion list rebuilt with {count} items.")
        message = f"Full sync complete. Built {count} exclusions."
    except Exception as e:
        logger.error(f"Exclusion builder failed: {e}")
        message = f"Sync completed with errors: {str(e)}"
    
    save_user_settings(settings)
    
    return {
        "status": "success",
        "message": message
    }
