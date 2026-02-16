import os
import glob
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MoverLogParser:
    def __init__(self, log_dir="/mover_logs"):
        self.log_dir = log_dir

    def get_latest_stats(self):
        """Compatibility wrapper for dashboard router calling get_latest_stats"""
        return self.get_stats_for_file()

    def get_all_runs(self):
        """Returns a list of all available mover logs for history picking"""
        try:
            files = glob.glob(f'{self.log_dir}/Filtered_files_*.list')
            return sorted([os.path.basename(f) for f in files], reverse=True)
        except Exception:
            return []

    def get_stats_for_file(self, filename=None):
        """Parses a specific log file or the latest one available"""
        try:
            if not filename:
                list_of_files = glob.glob(f'{self.log_dir}/Filtered_files_*.list')
                if not list_of_files:
                    list_of_files = glob.glob(f'{self.log_dir}/*.log')
                if not list_of_files: return None
                latest_file = max(list_of_files, key=os.path.getctime)
            else:
                latest_file = os.path.join(self.log_dir, filename)

            stats = {
                "filename": os.path.basename(latest_file),
                "excluded": 0,
                "moved": 0,
                "total_bytes_kept": 0,
                "timestamp": os.path.getmtime(latest_file),
                "efficiency": 0
            }

            with open(latest_file, 'r') as f:
                for line in f:
                    if "|" in line:
                        parts = line.strip().split("|")
                        if len(parts) >= 11:
                            status = parts[3].lower()
                            try:
                                size = int(parts[6])
                            except:
                                size = 0
                            if status == "skipped":
                                stats["excluded"] += 1
                                stats["total_bytes_kept"] += size
                            elif status == "yes":
                                stats["moved"] += 1
            
            total = stats["excluded"] + stats["moved"]
            if total > 0:
                stats["efficiency"] = round((stats["excluded"] / total) * 100, 1)
                
            return stats
        except Exception as e:
            logger.error(f"Failed to parse mover logs: {e}")
            return None

def get_mover_parser():
    return MoverLogParser()
