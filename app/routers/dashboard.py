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
    ca_mover_cache = ""
    last_mover_run = "N/A"
    if mover_stats:
        moved = mover_stats.get("files_moved", 0)
        used_pct = mover_stats.get("cache_used_pct", 0)
        free_gb = mover_stats.get("cache_free_gb", 0)
        total_gb = mover_stats.get("cache_total_gb", 0)
        threshold = mover_stats.get("move_threshold_pct", 90)
        move_status = mover_stats.get("move_status", "idle")
        test_mode = mover_stats.get("test_mode", False)
        ca_mover_cache = f"{used_pct}% used — {free_gb:.0f} GiB free of {total_gb:.0f} GiB"
        if move_status == "below_threshold":
            ca_mover_status = f"Below {threshold}% threshold — no move needed"
        elif move_status == "moved":
            ca_mover_status = f"{moved} files moved to array"
        elif move_status == "nothing_to_move":
            ca_mover_status = "Nothing to move"
        else:
            ca_mover_status = "Idle"
        if test_mode:
            ca_mover_status = "[DRY RUN] " + ca_mover_status
        ts = mover_stats.get("last_run", "")
        try:
            last_mover_run = datetime.datetime.strptime(ts, "%Y-%m-%dT%H%M%S").strftime("%Y-%m-%d %H:%M")
        except Exception:
            last_mover_run = ts
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
        "ca_mover_cache": ca_mover_cache,
        "last_mover_run": last_mover_run,
        "last_build": last_build
    })
