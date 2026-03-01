import logging
import threading
from app.core.config import get_user_settings
from app.services.alert_log import get_alert_log

logger = logging.getLogger(__name__)

_timers = {}
_timer_lock = threading.Lock()


def _do_rebuild(source: str):
    from app.services.exclusions import get_exclusion_manager
    alerts = get_alert_log()
    try:
        result = get_exclusion_manager().build_exclusions()
        total = result.get("total", 0)
        alerts.add("success", "builder", f"Exclusion build triggered by {source} completed — {total} exclusions written")
    except Exception as e:
        alerts.add("error", "builder", f"Exclusion build triggered by {source} FAILED: {e}")
        logger.error(f"[WEBHOOK] Build failed: {e}", exc_info=True)


def trigger_rebuild(source: str):
    settings = get_user_settings()
    alerts = get_alert_log()

    if not settings.webhooks.enabled:
        logger.info(f"[WEBHOOK] Webhooks disabled — ignoring trigger from {source}")
        return

    cooldown = settings.webhooks.cooldown_seconds
    alerts.add("info", "webhook", f"Webhook received from {source} — rebuild scheduled in {cooldown}s")
    logger.info(f"[WEBHOOK] Trigger from {source} — cooldown={cooldown}s")

    with _timer_lock:
        # Cancel existing timer if one is running
        if source in _timers and _timers[source] is not None:
            _timers[source].cancel()
            logger.info(f"[WEBHOOK] Cooldown reset for {source}")

        t = threading.Timer(cooldown, _do_rebuild, args=[source])
        t.daemon = True
        _timers[source] = t
        t.start()
