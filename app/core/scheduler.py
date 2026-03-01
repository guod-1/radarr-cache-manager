from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import get_user_settings, save_user_settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def run_sync_task():
    logger.info("[SCHEDULER] run_sync_task() triggered")
    try:
        from app.services.exclusions import get_exclusion_manager
        result = get_exclusion_manager().build_exclusions()
        logger.info(f"[SCHEDULER] Exclusion build complete: {result}")
    except Exception as e:
        logger.error(f"[SCHEDULER] Exclusion build FAILED: {e}", exc_info=True)
        return

    try:
        settings = get_user_settings()
        settings.exclusions.last_build = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_user_settings(settings)
        logger.info(f"[SCHEDULER] Sync timestamp saved: {settings.exclusions.last_build}")
    except Exception as e:
        logger.error(f"[SCHEDULER] Failed to save last_build timestamp: {e}", exc_info=True)


def run_stats_task():
    logger.info("[SCHEDULER] run_stats_task() triggered")
    try:
        from app.services.ca_mover import get_mover_parser
        parser = get_mover_parser()
        stats = parser.get_latest_stats()
        if stats:
            logger.info(f"[SCHEDULER] Stats refresh complete — excluded={stats.get('excluded', '?')} moved={stats.get('moved', '?')}")
        else:
            logger.info("[SCHEDULER] Stats refresh complete — no mover log files found yet")
    except Exception as e:
        logger.error(f"[SCHEDULER] Stats refresh FAILED: {e}", exc_info=True)
        return

    try:
        settings = get_user_settings()
        settings.exclusions.last_stats_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_user_settings(settings)
        logger.info(f"[SCHEDULER] Stats timestamp saved: {settings.exclusions.last_stats_update}")
    except Exception as e:
        logger.error(f"[SCHEDULER] Failed to save last_stats_update timestamp: {e}", exc_info=True)


class CacheScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.sync_id = "full_sync"
        self.monitor_id = "log_monitor"

    def start(self):
        settings = get_user_settings()
        sync_cron = settings.exclusions.full_sync_cron
        monitor_cron = settings.exclusions.log_monitor_cron

        logger.info(f"[SCHEDULER] Starting — sync_cron={sync_cron!r}  monitor_cron={monitor_cron!r}")

        self.scheduler.add_job(
            run_sync_task,
            CronTrigger.from_crontab(sync_cron),
            id=self.sync_id,
            misfire_grace_time=60
        )
        self.scheduler.add_job(
            run_stats_task,
            CronTrigger.from_crontab(monitor_cron),
            id=self.monitor_id,
            misfire_grace_time=60
        )
        self.scheduler.start()
        logger.info("[SCHEDULER] BackgroundScheduler started successfully")

    def reload_jobs(self):
        settings = get_user_settings()
        sync_cron = settings.exclusions.full_sync_cron
        monitor_cron = settings.exclusions.log_monitor_cron

        logger.info(f"[SCHEDULER] Reloading jobs — sync_cron={sync_cron!r}  monitor_cron={monitor_cron!r}")

        self.scheduler.reschedule_job(self.sync_id, trigger=CronTrigger.from_crontab(sync_cron))
        self.scheduler.reschedule_job(self.monitor_id, trigger=CronTrigger.from_crontab(monitor_cron))
        logger.info("[SCHEDULER] Jobs reloaded successfully")


scheduler_service = CacheScheduler()
