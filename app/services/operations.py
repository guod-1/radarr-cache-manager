import logging
from app.services.exclusions import get_exclusion_manager
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client

logger = logging.getLogger(__name__)

async def run_exclusion_logic():
    try:
        manager = get_exclusion_manager()
        # combine_exclusions returns an int (count), we need to handle that correctly
        count = manager.combine_exclusions()
        logger.info(f"Successfully combined {count} exclusions")
        return {"status": "success", "message": f"Combined {count} exclusions"}
    except Exception as e:
        logger.error(f"Exclusion builder failed: {e}")
        return {"status": "error", "message": str(e)}

async def run_full_sync():
    try:
        # Run exclusion build
        await run_exclusion_logic()
        
        # Add tag sync logic here if needed
        return {"status": "success", "message": "Full sync completed"}
    except Exception as e:
        logger.error(f"Full sync failed: {e}")
        return {"status": "error", "message": str(e)}
