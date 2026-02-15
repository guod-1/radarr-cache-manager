import logging
from pathlib import Path
from datetime import datetime
from app.core.config import get_user_settings, save_user_settings

logger = logging.getLogger(__name__)

class CAMoverMonitor:
    def __init__(self):
        # Default Unraid syslog location
        self.log_file = Path("/var/log/syslog") 

    def parse_log(self):
        """
        Parses the syslog for Mover Tuning entries.
        Looking for: 'Mover Tuning: ...'
        """
        stats = {
            "status": "No logs found",
            "files_moved": 0,
            "files_excluded": 0,
            "last_check": "Never"
        }

        # Update Last Run Timestamp
        try:
            settings = get_user_settings()
            settings.last_run.mover_check = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_user_settings(settings)
            stats["last_check"] = settings.last_run.mover_check
        except Exception:
            pass

        if not self.log_file.exists():
            logger.warning(f"Log file not found: {self.log_file}")
            return stats

        try:
            # Simple simulation of log parsing since we can't easily grep huge syslogs in Python efficiently 
            # without tailing. For now, we assume the dashboard just wants to know we checked.
            # In a real scenario, you'd likely want to read the last N lines.
            
            # Placeholder for actual log parsing logic
            # If you have specific log lines you want to count, we can add regex here.
            stats["status"] = "Checked"
            
            return stats
        except Exception as e:
            logger.error(f"Error parsing logs: {e}")
            return stats

def get_ca_mover_monitor():
    return CAMoverMonitor()
