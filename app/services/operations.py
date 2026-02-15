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
    
    try:
        excl = get_exclusion_manager()
        count = excl.combine_exclusions()
        
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
    
    messages = []
    
    # Test Radarr
    try:
        radarr_tags = get_radarr_client().get_all_tags()
        messages.append(f"Radarr: {len(radarr_tags)} tags found")
    except Exception as e:
        logger.error(f"Radarr sync failed: {e}")
        messages.append(f"Radarr: Failed - {str(e)}")
    
    # Test Sonarr
    try:
        sonarr_tags = get_sonarr_client().get_all_tags()
        messages.append(f"Sonarr: {len(sonarr_tags)} tags found")
    except Exception as e:
        logger.error(f"Sonarr sync failed: {e}")
        messages.append(f"Sonarr: Failed - {str(e)}")
    
    # Run Exclusion Builder
    try:
        excl = get_exclusion_manager()
        count = excl.combine_exclusions()
        logger.info(f"Exclusion list rebuilt with {count} items.")
        messages.append(f"Built {count} exclusions")
    except Exception as e:
        logger.error(f"Exclusion builder failed: {e}")
        messages.append(f"Exclusions: Failed - {str(e)}")
    
    return {
        "status": "success",
        "message": " | ".join(messages)
    }
