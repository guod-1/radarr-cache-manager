from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.ca_mover import get_mover_parser
from app.services.exclusions import get_exclusion_manager
import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    mover_parser = get_mover_parser()
    exclusion_manager = get_exclusion_manager()
    
    stats = mover_parser.get_latest_stats()
    cache_usage = mover_parser.get_cache_usage()
    exclusion_stats = exclusion_manager.get_exclusion_stats()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "cache_usage": cache_usage,
        "exclusion_count": exclusion_stats.get("total_count", 0),
        "radarr_online": True,
        "sonarr_online": True,
        "check_time": datetime.datetime.now().strftime("%H:%M:%S")
    })

@router.get("/stats/refresh", response_class=HTMLResponse)
async def refresh_stats(request: Request):
    # This must ONLY return the partial, not the full dashboard
    mover_parser = get_mover_parser()
    stats = mover_parser.get_latest_stats()
    return templates.TemplateResponse("partials/mover_stats_card.html", {
        "request": request, 
        "stats": stats, 
        "check_time": datetime.datetime.now().strftime("%H:%M:%S")
    })
