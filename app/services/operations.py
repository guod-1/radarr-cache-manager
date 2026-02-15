import logging
from app.services.exclusions import get_exclusion_manager
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client

logger = logging.getLogger(__name__)

async def run_exclusion_logic():
    """Builds and combines exclusion files"""
    try:
        manager = get_exclusion_manager()
        count = manager.combine_exclusions()
        logger.info(f"Successfully combined {count} exclusions")
        return {"status": "success", "message": f"Combined {count} exclusions"}
    except Exception as e:
        logger.error(f"Exclusion builder failed: {e}")
        return {"status": "error", "message": str(e)}

async def run_radarr_tag_operation():
    """Placeholder or implementation for Radarr tag syncing"""
    try:
        # Implementation logic here
        return {"status": "success", "message": "Radarr tag operation triggered"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def run_sonarr_tag_operation():
    """Placeholder or implementation for Sonarr tag syncing"""
    try:
        # Implementation logic here
        return {"status": "success", "message": "Sonarr tag operation triggered"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def run_full_sync():
    """Runs all operations in sequence"""
    try:
        await run_exclusion_logic()
        await run_radarr_tag_operation()
        await run_sonarr_tag_operation()
        return {"status": "success", "message": "Full sync completed"}
    except Exception as e:
        logger.error(f"Full sync failed: {e}")
        return {"status": "error", "message": str(e)}
