from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.ca_mover import get_mover_parser
from app.services.exclusions import get_exclusion_manager
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
import datetime
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def format_filesize(value):
    if not value: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if value < 1024.0:
            return f"{value:3.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    mover = get_mover_parser()
    excl = get_exclusion_manager()
    
    mover_stats = mover.get_latest_stats()
    disk_usage = mover.get_cache_usage()
    excl_stats = excl.get_exclusion_stats()
    
    last_check = datetime.datetime.fromtimestamp(mover_stats['timestamp']).strftime('%Y-%m-%d %H:%M') if mover_stats else "Never"
    last_run = "Never"
    if mover_stats and mover_stats['last_run_timestamp']:
        last_run = datetime.datetime.fromtimestamp(mover_stats['last_run_timestamp']).strftime('%Y-%m-%d %H:%M')
    
    last_build = "Never"
    exclusions_file = "/config/mover_exclusions.txt"
    if os.path.exists(exclusions_file):
        last_build = datetime.datetime.fromtimestamp(os.path.getmtime(exclusions_file)).strftime('%Y-%m-%d %H:%M')

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "radarr_connected": get_radarr_client().test_connection(),
        "sonarr_connected": get_sonarr_client().test_connection(),
        "cache_percent": disk_usage['percent'],
        "cache_free": format_filesize(disk_usage['free']),
        "ca_mover_excluded": mover_stats['excluded'] if mover_stats else 0,
        "ca_space_saved": format_filesize(mover_stats['total_bytes_kept']) if mover_stats else "0 B",
        "ca_mover_last_run": last_run,
        "ca_mover_last_check": last_check,
        "is_actual_run": mover_stats['is_run'] if mover_stats else False,
        "last_build": last_build,
        "exclusion_count": excl_stats.get("total_count", 0)
    })
