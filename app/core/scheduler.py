from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from app.core.config import get_user_settings

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.settings = get_user_settings()
        self._setup_jobs()

    def _setup_jobs(self):
        """Initializes the scheduler with user settings"""
        if self.settings.scheduler.enabled:
            try:
                # Main Cache Manager Job
                self.scheduler.add_job(
                    self._run_cache_manager,
                    CronTrigger.from_crontab(self.settings.scheduler.cron_expression),
                    id="cache_manager",
                    replace_existing=True
                )
                logger.info(f"Scheduled job with cron: {self.settings.scheduler.cron_expression}")
            except Exception as e:
                logger.error(f"Failed to schedule job: {e}")

    async def _run_cache_manager(self):
        """Wrapper to run the full sync logic"""
        try:
            # FIX: Use the correct function name 'run_full_sync'
            from app.services.operations import run_full_sync
            logger.info("Scheduler: Starting scheduled sync...")
            await run_full_sync()
            logger.info("Scheduler: Scheduled sync complete.")
        except Exception as e:
            logger.error(f"Scheduler failed: {e}")

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def update_schedule(self):
        """Reloads the schedule based on new settings"""
        self.settings = get_user_settings()
        self.scheduler.remove_all_jobs()
        self._setup_jobs()
        
        if not self.scheduler.running and self.settings.scheduler.enabled:
            self.scheduler.start()
        elif self.scheduler.running and not self.settings.scheduler.enabled:
            self.scheduler.shutdown()

    @property
    def running(self):
        return self.scheduler.running

    def get_next_run_time(self):
        job = self.scheduler.get_job("cache_manager")
        if job:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        return "Not Scheduled"

# Singleton instance
_scheduler_instance = None

def get_scheduler():
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerService()
    return _scheduler_instance
