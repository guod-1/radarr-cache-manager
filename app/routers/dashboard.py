from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.ca_mover import get_mover_parser
from app.services.exclusions import get_exclusion_manager
from app.core.config import get_user_settings
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    mover = get_mover_parser()
    excl = get_exclusion_manager()
    settings = get_user_settings()
    
    mover_stats = mover.get_latest_stats()
    excl_stats = excl.get_exclusion_stats()
    
    last_check = "N/A"
    status_text = "No logs found"
    if mover_stats:
        status_text = f"{mover_stats['excluded']} Excluded / {mover_stats['moved']} Moved"
        last_check = datetime.datetime.fromtimestamp(mover_stats['timestamp']).strftime('%Y-%m-%d %H:%M')

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "ca_mover_status": status_text,
        "exclusion_count": excl_stats.get("total_count", 0),
        "last_run_mover": last_check,
        "radarr_sync": settings.radarr.last_sync or "Never",
        "sonarr_sync": settings.sonarr.last_sync or "Never",
        "last_build": settings.exclusions.last_build or "Never"
    })
