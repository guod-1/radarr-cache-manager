import json
import os
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

ALERT_LOG_PATH = "/config/alert_log.json"
MAX_ALERTS = 50


class Alert:
    def __init__(self, level: str, source: str, message: str):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.level = level      # success, error, warning, info
        self.source = source    # radarr, sonarr, builder, webhook
        self.message = message

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "source": self.source,
            "message": self.message
        }


class AlertLog:
    def __init__(self):
        self.alerts: List[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(ALERT_LOG_PATH):
            try:
                with open(ALERT_LOG_PATH, "r") as f:
                    self.alerts = json.load(f)
                logger.debug(f"[ALERTS] Loaded {len(self.alerts)} alerts from disk")
            except Exception as e:
                logger.error(f"[ALERTS] Failed to load alert log: {e}")
                self.alerts = []

    def _save(self):
        try:
            tmp = ALERT_LOG_PATH + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self.alerts, f, indent=2)
            os.replace(tmp, ALERT_LOG_PATH)
        except Exception as e:
            logger.error(f"[ALERTS] Failed to save alert log: {e}")

    def add(self, level: str, source: str, message: str):
        alert = Alert(level, source, message)
        self.alerts.insert(0, alert.to_dict())
        self.alerts = self.alerts[:MAX_ALERTS]
        self._save()
        logger.info(f"[ALERTS] [{level.upper()}] {source}: {message}")

    def get_all(self) -> List[dict]:
        return self.alerts

    def clear(self):
        self.alerts = []
        self._save()


_alert_log = AlertLog()

def get_alert_log() -> AlertLog:
    return _alert_log
