from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import get_user_settings
from app.services.ca_mover import get_mover_parser
from app.services.exclusions import get_exclusion_manager
import urllib.request
import urllib.error

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def check_service(url, api_key):
    if not url or not api_key: return False
    try:
        # Simple timeout check to see if service is up
        target = f"{url.rstrip('/')}/api/v3/system/status?apiKey={api_key}"
        request = urllib.request.Request(target, method='HEAD')
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status == 200
    except:
        return False

@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    settings = get_user_settings()
    parser = get_mover_parser()
    
    # FORCE REFRESH: Parse the log file right now!
    # This ensures we don't show "0" just because the cron hasn't run yet.
    try:
        stats = parser.parse_log()
    except Exception:
        # If parsing fails (e.g. file locked/missing), return empty zeros
        stats = {"movie_count": 0, "tv_count": 0, "total_size": "0 GB"}

    # Check Service Health
    radarr_up = check_service(settings.radarr.url, settings.radarr.api_key)
    sonarr_up = check_service(settings.sonarr.url, settings.sonarr.api_key)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "settings": settings,
        "stats": stats,
        "radarr_up": radarr_up,
        "sonarr_up": sonarr_up
    })

@router.post("/run-builder")
async def trigger_builder(background_tasks: BackgroundTasks):
    manager = get_exclusion_manager()
    background_tasks.add_task(manager.build_exclusions)
    return RedirectResponse(url="/dashboard", status_code=303)
