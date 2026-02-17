from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.core.config import get_user_settings
import logging

logger = logging.getLogger(__name__)

class CacheScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.full_sync_job_id = "full_sync_job"
        self.log_monitor_job_id = "log_monitor_job"

    def start(self):
        settings = get_user_settings()
        
        # Internal imports to prevent circular dependency
        from app.services.exclusions import run_full_operation
        from app.services.ca_mover import check_ca_mover_logs

        # 1. Schedule Full Sync (Cron)
        cron_val = settings.exclusions.full_sync_cron or "0 * * * *"
        self.scheduler.add_job(
            run_full_operation,
            CronTrigger.from_crontab(cron_val),
            id=self.full_sync_job_id,
            replace_existing=True
        )
        
        # 2. Schedule Log Monitor (Interval)
        interval_val = int(settings.exclusions.log_monitor_interval or 300)
        self.scheduler.add_job(
            check_ca_mover_logs,
            IntervalTrigger(seconds=interval_val),
            id=self.log_monitor_job_id,
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler started: Full Sync ({cron_val}), Log Monitor ({interval_val}s)")

    def reload_jobs(self):
        settings = get_user_settings()
        
        # Update Full Sync
        cron_val = settings.exclusions.full_sync_cron or "0 * * * *"
        self.scheduler.reschedule_job(
            self.full_sync_job_id, 
            trigger=CronTrigger.from_crontab(cron_val)
        )
        
        # Update Log Monitor
        interval_val = int(settings.exclusions.log_monitor_interval or 300)
        self.scheduler.reschedule_job(
            self.log_monitor_job_id, 
            trigger=IntervalTrigger(seconds=interval_val)
        )
        logger.info("Scheduler jobs reloaded with new settings.")

    def shutdown(self):
        self.scheduler.shutdown()

# This must match what main.py and your routers are importing
scheduler_service = CacheScheduler()
