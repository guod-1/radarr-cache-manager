import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import get_user_settings
from app.services.operations import run_full_sync

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        # Changed to AsyncIOScheduler (standard name)
        self.scheduler = AsyncIOScheduler()

    def start(self):
        settings = get_user_settings()
        if settings.scheduler.enabled:
            # We add a standard job that calls our non-async sync function
            self.scheduler.add_job(
                self._run_sync_job, 
                'cron', 
                id='mover_sync',
                replace_existing=True,
                **self._parse_cron(settings.scheduler.cron_expression)
            )
            self.scheduler.start()
            logger.info(f"Scheduler started with cron: {settings.scheduler.cron_expression}")

    def _run_sync_job(self):
        logger.info("Scheduler: Starting scheduled sync...")
        try:
            # Call the synchronous function
            run_full_sync()
            logger.info("Scheduler: Scheduled sync complete.")
        except Exception as e:
            logger.error(f"Scheduler failed: {e}")

    def _parse_cron(self, cron_str):
        parts = cron_str.split()
        if len(parts) < 5:
             return {'minute': '0', 'hour': '*/6'}
        return {
            'minute': parts[0],
            'hour': parts[1],
            'day': parts[2],
            'month': parts[3],
            'day_of_week': parts[4]
        }

scheduler_service = SchedulerService()
