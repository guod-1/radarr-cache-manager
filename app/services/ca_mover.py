import os
import logging
import shutil
from app.core.config import get_user_settings

logger = logging.getLogger(__name__)

def format_size(size_bytes):
    if size_bytes == "Unknown": return "0 B"
    try:
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
    except: return "0 B"

class MoverLogParser:
    def __init__(self, log_dir="/mover_logs"):
        self.log_dir = log_dir

    def _get_files_by_type(self):
        true_runs, idle_checks = [], []
        if not os.path.exists(self.log_dir): return [], []
        for entry in os.scandir(self.log_dir):
            if entry.name.startswith("Filtered_files_") and entry.name.endswith(".list"):
                timestamp_str = entry.name.replace("Filtered_files_", "").replace(".list", "")
                log_set = {
                    "timestamp": timestamp_str,
                    "mtime": entry.stat().st_mtime,
                    "list_path": entry.path,
                    "log_path": os.path.join(self.log_dir, f"Mover_tuning_{timestamp_str}.log")
                }
                if entry.stat().st_size > 500: true_runs.append(log_set)
                else: idle_checks.append(log_set)
        return sorted(true_runs, key=lambda x: x['mtime'], reverse=True), \
               sorted(idle_checks, key=lambda x: x['mtime'], reverse=True)

    def get_latest_stats(self):
        true_runs, idle_checks = self._get_files_by_type()
        latest = true_runs[0] if true_runs else (idle_checks[0] if idle_checks else None)
        if not latest: return None
        
        is_true = latest in true_runs
        stats = {
            "filename": os.path.basename(latest['log_path']),
            "type_label": "True-Mover Run" if is_true else "Idle-Mover Check",
            "is_run": is_true,
            "excluded": 0,
            "moved": 0,
            "timestamp": latest['mtime'],
            "protected_files": []
        }

        try:
            with open(latest['list_path'], 'r') as f:
                for line in f:
                    if "|" in line:
                        parts = [p.strip() for p in line.split("|")]
                        # Column 3 is status. If skipped, Column 4 is usually Path, Column 6 is size.
                        if len(parts) >= 11:
                            status = parts[3].lower()
                            if status == "skipped":
                                stats["excluded"] += 1
                                # We want the actual Path (often index 4 or 10)
                                path_val = parts[10] if len(parts[10]) > 5 else parts[4]
                                stats["protected_files"].append({
                                    "path": path_val,
                                    "size": format_size(parts[6])
                                })
                            elif status == "yes":
                                stats["moved"] += 1
            return stats
        except Exception as e:
            logger.error(f"Failed to parse list: {e}")
            return stats

    def get_cache_usage(self):
        try:
            settings = get_user_settings()
            usage = shutil.disk_usage(settings.exclusions.cache_mount_path or "/mnt/cache")
            percent = (usage.used / usage.total) * 100 if usage.total > 0 else 0
            return {"percent": round(percent, 1), "used": usage.used}
        except: return {"percent": 0, "used": 0}

def get_mover_parser():
    return MoverLogParser()
