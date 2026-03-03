from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.ca_mover import get_mover_parser
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.services.stats_cache import get_stats_cache
import datetime
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    mover = get_mover_parser()
    
    # Test connections (fast - just pings the API)
    radarr_connected = get_radarr_client().test_connection()
    sonarr_connected = get_sonarr_client().test_connection()
    
    # Get counts from cache (reads from exclusion file)
    cache = get_stats_cache()
    cache.refresh_from_file()  # Quick file read
    counts = cache.get_counts()
    
    # Get CA Mover stats
    mover_stats = mover.get_latest_stats()
    
    ca_mover_status = "No logs found"
    last_mover_run = "N/A"
    if mover_stats:
        filtered = mover_stats.get("files_filtered", 0)
        moved = mover_stats.get("files_moved", 0)
        ca_mover_status = f"{filtered} Files Evaluated / {moved} Files Moved to Array"
        ts = mover_stats.get("last_run", "")
        try:
            last_mover_run = datetime.datetime.strptime(ts, "%Y-%m-%dT%H%M%S").strftime("%Y-%m-%d %H:%M")
        except Exception:
            last_mover_run = ts
    
    # Get last build time from file
    last_build = "Never"
    exclusions_file = "/config/mover_exclusions.txt"
    if os.path.exists(exclusions_file):
        mtime = os.path.getmtime(exclusions_file)
        last_build = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "radarr_up": radarr_connected,
        "sonarr_up": sonarr_connected,
        "movie_count": counts['movie_count'],
        "tv_count": counts['tv_count'],
        "exclusion_count": counts['total_count'],
        "ca_mover_status": ca_mover_status,
        "last_mover_run": last_mover_run,
        "last_build": last_build
    })
