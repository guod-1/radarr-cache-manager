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
        """Calculates disk usage for the configured cache drive mount point"""
        try:
            settings = get_user_settings()
            path = settings.exclusions.cache_mount_path
            
            if not os.path.exists(path):
                logger.error(f"Configured cache path {path} does not exist")
                return {"total": 1, "used": 0, "free": 0, "percent": 0}
                
            usage = shutil.disk_usage(path)
            percent = (usage.used / usage.total) * 100 if usage.total > 0 else 0
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": round(percent, 1)
            }
        except Exception as e:
            logger.error(f"Failed to get cache usage: {e}")
            return {"total": 1, "used": 0, "free": 0, "percent": 0}

    def get_latest_stats(self):
        try:
            list_of_files = glob.glob(f'{self.log_dir}/Filtered_files_*.list')
            if not list_of_files:
                list_of_files = glob.glob(f'{self.log_dir}/*.log')
            if not list_of_files: return None
            
            latest_file = max(list_of_files, key=os.path.getctime)
            
            run_file = None
            for f in sorted(list_of_files, key=os.path.getctime, reverse=True):
                if os.path.getsize(f) > 500:
                    run_file = f
                    break
            
            stats = {
                "filename": os.path.basename(latest_file),
                "is_run": os.path.getsize(latest_file) > 500,
                "excluded": 0,
                "moved": 0,
                "total_bytes_kept": 0,
                "timestamp": os.path.getmtime(latest_file),
                "last_run_timestamp": os.path.getmtime(run_file) if run_file else None
            }

            with open(latest_file, 'r') as f:
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
            logger.error(f"Failed to parse mover logs: {e}")
            return None

def get_mover_parser():
    return MoverLogParser()
