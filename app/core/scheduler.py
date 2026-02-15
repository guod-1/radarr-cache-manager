"""
Scheduler

Handles scheduled execution of the cache manager using APScheduler with cron expressions.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from app.core.config import get_user_settings

logger = logging.getLogger(__name__)


class CacheScheduler:
    """Scheduler for automatic cache manager runs"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.job_id = "cache_manager_job"
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
            self._update_job()
    
    def shutdown(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def _update_job(self):
        """Update or add the scheduled job based on current settings"""
        settings = get_user_settings().scheduler
        
        # Remove existing job if it exists
        if self.scheduler.get_job(self.job_id):
            self.scheduler.remove_job(self.job_id)
            logger.info(f"Removed existing job: {self.job_id}")
        
        # Add new job if enabled
        if settings.enabled:
            try:
                trigger = CronTrigger.from_crontab(settings.cron_expression)
                self.scheduler.add_job(
                    self._run_cache_manager,
                    trigger=trigger,
                    id=self.job_id,
                    name="Cache Manager",
                    replace_existing=True
                )
                logger.info(f"Scheduled job with cron: {settings.cron_expression}")
            except Exception as e:
                logger.error(f"Failed to schedule job: {e}")
    
    def _run_cache_manager(self):
        """Execute the cache manager operation"""
        # Import here to avoid circular dependencies
        from app.services.operations import run_full_operation
        
        logger.info("Scheduled run started")
        try:
            result = run_full_operation()
            logger.info(f"Scheduled run completed: {result}")
        except Exception as e:
            logger.error(f"Scheduled run failed: {e}")
    
    def update_schedule(self):
        """Update the schedule when settings change"""
        if self.scheduler.running:
            self._update_job()
    
    def get_next_run_time(self) -> str:
        """Get the next scheduled run time"""
        job = self.scheduler.get_job(self.job_id)
        if job and job.next_run_time:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        return "Not scheduled"
    
    @property
    def running(self) -> bool:
        """Check if scheduler is running"""
        return self.scheduler.running


# Global scheduler instance
scheduler = CacheScheduler()


def get_scheduler() -> CacheScheduler:
    """Dependency for FastAPI routes"""
    return scheduler
