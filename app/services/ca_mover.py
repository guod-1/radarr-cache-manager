import os
import logging
import shutil
from datetime import datetime
from app.core.config import get_user_settings

logger = logging.getLogger(__name__)


class CAMoverParser:
    def __init__(self, log_dir="/mover_logs"):
        self.log_dir = log_dir

    def _get_latest_files(self):
        """Find the most recent set of mover log files."""
        if not os.path.exists(self.log_dir):
            return None
        runs = {}
        for entry in os.scandir(self.log_dir):
            for prefix in ("Summary_", "Filtered_files_", "Mover_action_"):
                if entry.name.startswith(prefix) and entry.name.endswith((".txt", ".list")):
                    ts = entry.name.replace(prefix, "").replace(".txt", "").replace(".list", "")
                    if ts not in runs:
                        runs[ts] = {"timestamp": ts, "mtime": entry.stat().st_mtime}
                    runs[ts][prefix.rstrip("_").lower()] = entry.path
        if not runs:
            return None
        return sorted(runs.values(), key=lambda x: x["mtime"], reverse=True)[0]

    def get_latest_stats(self):
        """Parse the most recent mover run and return stats dict."""
        run = self._get_latest_files()
        if not run:
            logger.debug("[CA_MOVER] No mover log files found")
            return None
        stats = {
            "timestamp": run["timestamp"],
            "files_moved": 0,
            "size_moved": 0,
            "files_filtered": 0,
            "last_run": run["timestamp"]
        }
        # Parse Summary for files moved
        summary_path = run.get("summary")
        if summary_path and os.path.exists(summary_path):
            try:
                with open(summary_path) as f:
                    lines = f.readlines()
                if len(lines) >= 2:
                    headers = lines[0].strip().split("|")
                    for line in lines[1:]:
                        parts = line.strip().split("|")
                        if parts[0] == "TOTAL" and len(parts) == len(headers):
                            row = dict(zip(headers, parts))
                            stats["files_moved"] = int(row.get("FILES_FROM_PRIMARY", 0) or 0)
                            stats["size_moved"] = int(row.get("SIZE_FROM_PRIMARY", 0) or 0)
            except Exception as e:
                logger.error(f"[CA_MOVER] Failed to parse Summary: {e}")

        # Parse Filtered_files for exclusion count
        filtered_path = run.get("filtered_files")
        if filtered_path and os.path.exists(filtered_path):
            try:
                with open(filtered_path) as f:
                    lines = f.readlines()
                # Count non-header, non-empty lines
                stats["files_filtered"] = max(0, len([l for l in lines if l.strip() and not l.startswith("PRIMARY")]) )
            except Exception as e:
                logger.error(f"[CA_MOVER] Failed to parse Filtered_files: {e}")

        # Cache disk usage
        try:
            settings = get_user_settings()
            cache_path = settings.exclusions.cache_mount_path or "/mnt/cache"
            usage = shutil.disk_usage(cache_path)
            stats["cache_used_pct"] = round(usage.used / usage.total * 100, 1)
            stats["cache_free_gb"] = round(usage.free / (1024**3), 1)
            stats["cache_total_gb"] = round(usage.total / (1024**3), 1)
        except Exception as e:
            logger.debug(f"[CA_MOVER] Could not get disk usage: {e}")

        # Parse Mover_action for action breakdown
        action_path = run.get("mover_action")
        if action_path and os.path.exists(action_path):
            try:
                actions = {}
                with open(action_path) as f:
                    lines = f.readlines()
                headers = lines[0].strip().split("|") if lines else []
                for line in lines[1:]:
                    parts = line.strip().split("|")
                    if len(parts) >= len(headers):
                        row = dict(zip(headers, parts))
                        action = row.get("ACTION", "unknown")
                        actions[action] = actions.get(action, 0) + 1
                stats["actions"] = actions
            except Exception as e:
                logger.error(f"[CA_MOVER] Failed to parse Mover_action: {e}")

        # Parse mover log for threshold and status
        log_path = run.get("mover_tuning")
        if not log_path:
            # try alternate key
            for k, v in run.items():
                if isinstance(v, str) and v.endswith(".log"):
                    log_path = v
                    break
        if log_path and os.path.exists(log_path):
            try:
                with open(log_path) as f:
                    log_text = f.read()
                stats["test_mode"] = "Test Mode: yes" in log_text
                if "Pool is below moving threshold" in log_text:
                    stats["move_status"] = "below_threshold"
                elif "No new files will be moved" in log_text:
                    stats["move_status"] = "nothing_to_move"
                elif stats["files_moved"] > 0:
                    stats["move_status"] = "moved"
                else:
                    stats["move_status"] = "idle"
                # Extract threshold percentage
                import re
                match = re.search(r'moving threshold percentage:\s+(\d+)%', log_text)
                if match:
                    stats["cache_used_pct_at_run"] = int(match.group(1))
                match2 = re.search(r'Moving threshold: (\d+)%', log_text)
                if match2:
                    stats["move_threshold_pct"] = int(match2.group(1))
            except Exception as e:
                logger.error(f"[CA_MOVER] Failed to parse mover log: {e}")

        logger.info(f"[CA_MOVER] Parsed run {stats['timestamp']} — moved={stats['files_moved']} filtered={stats['files_filtered']}")
        return stats


_parser_instance = None

def get_mover_parser():
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = CAMoverParser()
    return _parser_instance
