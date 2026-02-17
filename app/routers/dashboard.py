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


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    mover = get_mover_parser()
    excl = get_exclusion_manager()
    
    # Test connections
    radarr_client = get_radarr_client()
    sonarr_client = get_sonarr_client()
    radarr_connected = radarr_client.test_connection()
    sonarr_connected = sonarr_client.test_connection()
    
    # Count movies with excluded tags
    movie_count = 0
    tv_count = 0
    
    try:
        from app.core.config import get_user_settings
        settings = get_user_settings()
        
        # Count Radarr movies with exclusion tags
        if radarr_connected and settings.exclusions.radarr_exclude_tag_ids:
            all_movies = radarr_client.get_all_movies()
            for movie in all_movies:
                movie_tags = movie.get('tags', [])
                if any(tag_id in settings.exclusions.radarr_exclude_tag_ids for tag_id in movie_tags):
                    movie_count += 1
        
        # Count Sonarr shows with exclusion tags
        if sonarr_connected and settings.exclusions.sonarr_exclude_tag_ids:
            all_series = sonarr_client.get_all_series()
            for series in all_series:
                series_tags = series.get('tags', [])
                if any(tag_id in settings.exclusions.sonarr_exclude_tag_ids for tag_id in series_tags):
                    tv_count += 1
    except Exception as e:
        import logging
        logging.error(f"Error counting protected items: {e}")
    
    # Get CA Mover stats
    mover_stats = mover.get_latest_stats()
    excl_stats = excl.get_exclusion_stats()
    
    ca_mover_status = "No logs found"
    last_mover_run = "N/A"
    if mover_stats:
        ca_mover_status = f"{mover_stats['excluded']} Excluded / {mover_stats['moved']} Moved"
        last_mover_run = datetime.datetime.fromtimestamp(mover_stats['timestamp']).strftime('%Y-%m-%d %H:%M')
    
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
        "movie_count": movie_count,
        "tv_count": tv_count,
        "exclusion_count": excl_stats.get("total_count", 0),
        "ca_mover_status": ca_mover_status,
        "last_mover_run": last_mover_run,
        "last_build": last_build
    })
