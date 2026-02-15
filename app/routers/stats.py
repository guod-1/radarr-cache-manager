from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.ca_mover import get_mover_parser
from app.services.exclusions import get_exclusion_manager
import datetime
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def format_datetime(value):
    if value is None: return "N/A"
    return datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M')

def format_filesize(value):
    if not value: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if value < 1024.0:
            return f"{value:3.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"

templates.env.filters["datetime"] = format_datetime
templates.env.filters["filesize"] = format_filesize

@router.get("/", response_class=HTMLResponse)
async def stats_page(request: Request):
    mover = get_mover_parser()
    mover_stats = mover.get_latest_stats()
    
    # Extract detailed file list from the log for the UI
    excluded_files = []
    if mover_stats and 'filename' in mover_stats:
        log_path = os.path.join("/mover_logs", mover_stats['filename'])
        try:
            with open(log_path, 'r') as f:
                for line in f:
                    if "|" in line:
                        parts = line.strip().split("|")
                        if len(parts) >= 11 and parts[3].lower() == "skipped":
                            excluded_files.append({
                                "path": parts[10],
                                "size": int(parts[6]) if parts[6].isdigit() else 0
                            })
        except Exception as e:
            logger.error(f"Error reading file list for stats: {e}")

    return templates.TemplateResponse("stats.html", {
        "request": request,
        "mover": mover_stats,
        "bytes_kept": mover_stats.get('total_bytes_kept', 0) if mover_stats else 0,
        "excluded_files": sorted(excluded_files, key=lambda x: x['size'], reverse=True)
    })
