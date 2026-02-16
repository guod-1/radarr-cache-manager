from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.ca_mover import get_mover_parser
from app.services.exclusions import get_exclusion_manager
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    mover_parser = get_mover_parser()
    exclusion_manager = get_exclusion_manager()
    stats = mover_parser.get_latest_stats()
    cache_usage = mover_parser.get_cache_usage()
    exclusion_count = (exclusion_manager.get_exclusion_stats() or {}).get("total_count", 0)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "cache_usage": cache_usage,
        "exclusion_count": exclusion_count,
        "radarr_online": True,
        "sonarr_online": True,
        "check_time": datetime.datetime.now().strftime("%H:%M:%S")
    })

@router.get("/stats/refresh", response_class=HTMLResponse)
async def refresh_stats(request: Request):
    # This specifically calls ONLY the partial file
    mover_parser = get_mover_parser()
    stats = mover_parser.get_latest_stats()
    return templates.TemplateResponse("partials/mover_stats_card.html", {
        "request": request, 
        "stats": stats, 
        "check_time": datetime.datetime.now().strftime("%H:%M:%S")
    })
