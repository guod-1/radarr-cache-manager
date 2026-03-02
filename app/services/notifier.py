import logging
import requests
import concurrent.futures
from datetime import datetime

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

logger = logging.getLogger(__name__)

LEVEL_COLORS = {
    "success": 0x2ecc71,
    "error": 0xe74c3c,
    "warning": 0xf39c12,
    "info": 0x3498db
}

LEVEL_ICONS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "📥"
}


def _send_discord_sync(url: str, level: str, source: str, message: str):
    """Run in thread executor — never call directly from async context."""
    if not url:
        return
    try:
        embed = {
            "title": f"{LEVEL_ICONS.get(level, '🔔')} MTEM — {source.upper()}",
            "description": message,
            "color": LEVEL_COLORS.get(level, 0x95a5a6),
            "footer": {"text": f"Mover Tuning Exclusion Manager · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        }
        payload = {"embeds": [embed]}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.debug(f"[NOTIFIER] Discord notification sent: {level} - {message}")
    except Exception as e:
        logger.error(f"[NOTIFIER] Failed to send Discord notification: {e}")


def _send_discord_sync(url: str, level: str, source: str, message: str):
    """Run in thread executor — never call directly from async context."""
    """Non-blocking wrapper — submits to thread pool."""
    _executor.submit(_send_discord_sync, url, level, source, message)


def send_discord_notification(url: str, level: str, source: str, message: str):
    """Non-blocking wrapper — submits to thread pool."""
    _executor.submit(_send_discord_sync, url, level, source, message)


def notify(level: str, source: str, message: str):
    from app.core.config import get_user_settings
    settings = get_user_settings()
    if not settings.webhooks.discord_enabled:
        return
    if not settings.webhooks.discord_webhook_url:
        return
    if level == "warning" and not settings.webhooks.discord_notify_warnings:
        return
    send_discord_notification(
        settings.webhooks.discord_webhook_url,
        level,
        source,
        message
    )


class DiscordLogHandler(logging.Handler):
    """
    Logging handler that forwards ERROR and optionally WARNING
    log messages to Discord automatically.
    """
    _emitting = False

    def emit(self, record: logging.LogRecord):
        if self.__class__._emitting:
            return
        if record.name.startswith("app.services.notifier") or record.name.startswith("app.core.config"):
            return
        self.__class__._emitting = True
        try:
            from app.core.config import get_user_settings
            settings = get_user_settings()
            if not settings.webhooks.discord_enabled:
                return
            if not settings.webhooks.discord_webhook_url:
                return
            if record.levelno == logging.ERROR:
                level = "error"
            elif record.levelno == logging.WARNING and settings.webhooks.discord_notify_warnings:
                level = "warning"
            else:
                return
            source = record.name.split(".")[-1]
            message = self.format(record)
            send_discord_notification(
                settings.webhooks.discord_webhook_url,
                level,
                source,
                message[:1900]
            )
        except Exception:
            pass
        finally:
            self.__class__._emitting = False
