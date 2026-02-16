import os
import glob
import logging
import shutil
import datetime
from app.core.config import get_user_settings

logger = logging.getLogger(__name__)

class MoverLogParser:
    def __init__(self, log_dir="/mover_logs"):
        self.log_dir = log_dir

    def get_cache_usage(self):
        try:
            settings = get_user_settings()
            path = settings.exclusions.cache_mount_path
            if not path or not os.path.exists(path):
                return {"total": 1, "used": 0, "free": 0, "percent": 0}
            usage = shutil.disk_usage(path)
            percent = (usage.used / usage.total) * 100 if usage.total > 0 else 0
            return {
                "total": usage.total, "used": usage.used, "free": usage.free, "percent": round(percent, 1)
            }
        except Exception:
            return {"total": 1, "used": 0, "free": 0, "percent": 0}

    def _get_latest_file(self, pattern):
        """Finds the most recent file matching a pattern in the log directory"""
        files = glob.glob(os.path.join(self.log_dir, pattern))
        if not files:
            return None
        return max(files, key=os.path.getmtime)

    def get_latest_stats(self):
        try:
            # Look for the latest Mover Tuning log
            latest_log = self._get_latest_file("Mover_tuning_*.log")
            # Look for the latest Filtered list (which tells us what was skipped/moved)
            latest_list = self._get_latest_file("Filtered_files_*.list")
            
            if not latest_log or not latest_list:
                return None
            
            stats = {
                "filename": os.path.basename(latest_log),
                "is_run": os.path.getsize(latest_list) > 500, # If list is tiny, it was just a check
                "excluded": 0,
                "moved": 0,
                "total_bytes_kept": 0,
                "timestamp": os.path.getmtime(latest_log),
                "last_run_timestamp": os.path.getmtime(latest_list)
            }

            with open(latest_list, 'r') as f:
                for line in f:
                    if "|" in line:
                        parts = line.strip().split("|")
                        if len(parts) >= 11:
                            status = parts[3].lower()
                            size = int(parts[6]) if parts[6].isdigit() else 0
                            if status == "skipped":
                                stats["excluded"] += 1
                                stats["total_bytes_kept"] += size
                            elif status == "yes":
                                stats["moved"] += 1
            return stats
        except Exception as e:
            logger.error(f"Failed to parse timestamped mover logs: {e}")
            return None

def get_mover_parser():
    return MoverLogParser()
