import os
import glob
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MoverLogParser:
    def __init__(self, log_dir="/mover_logs"):
        self.log_dir = log_dir

    def get_latest_stats(self):
        try:
            # Prioritize the specific Filtered_files_ logs
            list_of_files = glob.glob(f'{self.log_dir}/Filtered_files_*.list')
            if not list_of_files:
                list_of_files = glob.glob(f'{self.log_dir}/*.log')
                
            if not list_of_files:
                return None

            latest_file = max(list_of_files, key=os.path.getctime)
            filename = os.path.basename(latest_file)
            
            stats = {
                "filename": filename,
                "excluded": 0,
                "moved": 0,
                "total_bytes_kept": 0,
                "timestamp": os.path.getmtime(latest_file)
            }

            with open(latest_file, 'r') as f:
                for line in f:
                    # Handle the piped-delimiter table format
                    if "|" in line:
                        parts = line.strip().split("|")
                        if len(parts) >= 11:
                            # Column 4 (index 3) is SHAREUSECACHE
                            status = parts[3].lower()
                            # Column 7 (index 6) is FILESIZE
                            try:
                                size = int(parts[6])
                            except:
                                size = 0

                            if status == "skipped":
                                stats["excluded"] += 1
                                stats["total_bytes_kept"] += size
                            elif status == "yes":
                                stats["moved"] += 1
                    
                    # Fallback for standard logs
                    else:
                        line_low = line.lower()
                        if any(x in line_low for x in ["skipping", "not moving", "ignoring"]):
                            stats["excluded"] += 1
                        elif "moving" in line_low:
                            stats["moved"] += 1
            
            return stats
        except Exception as e:
            logger.error(f"Failed to parse mover logs: {e}")
            return None

def get_mover_parser():
    return MoverLogParser()
