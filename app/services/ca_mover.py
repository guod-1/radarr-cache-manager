"""
CA Mover Tuning Service

Monitors CA Mover Tuning plugin logs to verify exclusions are working
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class CAMoverMonitor:
    """Monitor CA Mover Tuning plugin logs"""
    
    def __init__(self, log_dir: str = "/config/ca-logs/ca.mover.tuning"):
        self.log_dir = Path(log_dir)
    
    def get_latest_summary(self) -> Path:
        """Find the most recent Summary file"""
        if not self.log_dir.exists():
            return None
        
        summary_files = list(self.log_dir.glob("Summary_*.txt"))
        if not summary_files:
            return None
        
        # Sort by name (timestamp in filename), most recent first
        summary_files.sort(reverse=True)
        return summary_files[0]
    
    def get_latest_filtered(self) -> Path:
        """Find the most recent Filtered_files list"""
        if not self.log_dir.exists():
            return None
        
        filtered_files = list(self.log_dir.glob("Filtered_files_*.list"))
        if not filtered_files:
            return None
        
        filtered_files.sort(reverse=True)
        return filtered_files[0]
    
    def parse_log(self) -> dict:
        """
        Parse the latest CA Mover Tuning logs
        
        Returns dict with:
        - status: 'working', 'not_configured', 'no_logs', 'error'
        - files_moved: number of files moved from cache
        - files_excluded: number of files excluded/filtered
        - last_run: timestamp of last run
        - cache_name: name of cache drive
        """
        result = {
            'status': 'no_logs',
            'files_moved': 0,
            'files_excluded': 0,
            'last_run': None,
            'cache_name': None,
            'size_moved': 0
        }
        
        # Check for summary file
        summary_file = self.get_latest_summary()
        if not summary_file:
            logger.warning("No CA Mover Tuning summary files found")
            return result
        
        try:
            # Parse summary file
            with open(summary_file, 'r') as f:
                lines = f.readlines()
            
            # Get timestamp from filename
            timestamp_str = summary_file.stem.replace('Summary_', '')
            try:
                result['last_run'] = datetime.strptime(timestamp_str, '%Y-%m-%dT%H%M%S')
            except:
                result['last_run'] = datetime.fromtimestamp(summary_file.stat().st_mtime)
            
            # Parse CSV data (skip header)
            if len(lines) >= 2:
                # Second line has the data
                data_line = lines[1].strip().split('|')
                if len(data_line) >= 4:
                    result['cache_name'] = data_line[0]
                    result['files_moved'] = int(data_line[1])
                    result['size_moved'] = int(data_line[2])
            
            # Count excluded files from Filtered_files list
            filtered_file = self.get_latest_filtered()
            if filtered_file and filtered_file.exists():
                with open(filtered_file, 'r') as f:
                    filtered_lines = f.readlines()
                result['files_excluded'] = len([l for l in filtered_lines if l.strip()])
            
            # Determine status
            if result['files_excluded'] > 0:
                result['status'] = 'working'
            elif result['files_moved'] >= 0:
                result['status'] = 'configured'
            else:
                result['status'] = 'not_configured'
            
            logger.info(f"CA Mover status: {result['status']}, moved: {result['files_moved']}, excluded: {result['files_excluded']}")
            
        except Exception as e:
            logger.error(f"Error parsing CA Mover logs: {e}")
            result['status'] = 'error'
        
        return result
    
    def is_recent_run(self, hours: int = 24) -> bool:
        """Check if CA Mover ran within the last N hours"""
        summary_file = self.get_latest_summary()
        if not summary_file:
            return False
        
        mod_time = datetime.fromtimestamp(summary_file.stat().st_mtime)
        return datetime.now() - mod_time < timedelta(hours=hours)
    
    def format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"


def get_ca_mover_monitor() -> CAMoverMonitor:
    """Dependency for FastAPI routes"""
    return CAMoverMonitor()
