"""
Simple stats from the exclusion file
"""
import logging
import os

logger = logging.getLogger(__name__)

class StatsCache:
    def __init__(self):
        self.movie_count = 0
        self.tv_count = 0
        self.total_count = 0
        self.last_update = None
    
    def refresh_from_file(self):
        """Read exclusion file and count movies vs TV"""
        movie_count = 0
        tv_count = 0
        total_count = 0
        
        exclusions_file = "/config/mover_exclusions.txt"
        if os.path.exists(exclusions_file):
            try:
                with open(exclusions_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        total_count += 1
                        
                        # Count based on path patterns
                        line_lower = line.lower()
                        if '/movies/' in line_lower or '/movie/' in line_lower:
                            movie_count += 1
                        elif '/tv/' in line_lower or '/shows/' in line_lower or '/series/' in line_lower:
                            tv_count += 1
                
                self.movie_count = movie_count
                self.tv_count = tv_count
                self.total_count = total_count
                
                import datetime
                self.last_update = datetime.datetime.now()
                
                logger.info(f"Stats updated: {movie_count} movies, {tv_count} TV, {total_count} total exclusions")
            except Exception as e:
                logger.error(f"Error reading exclusion file: {e}")
    
    def get_counts(self):
        """Get current counts"""
        return {
            "movie_count": self.movie_count,
            "tv_count": self.tv_count,
            "total_count": self.total_count,
            "last_update": self.last_update
        }

# Singleton instance
_stats_cache = StatsCache()

def get_stats_cache():
    return _stats_cache
