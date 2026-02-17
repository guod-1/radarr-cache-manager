from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import get_user_settings
from app.services.ca_mover import get_mover_parser
from app.services.exclusions import get_exclusion_manager
import httpx

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

async def check_service(url, api_key):
    if not url or not api_key: return False
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url.rstrip('/')}/api/v3/system/status", params={"apiKey": api_key}, timeout=2)
            return response.status_code == 200
    except:
        return False

@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    settings = get_user_settings()
    stats = get_mover_parser().get_latest_stats()
    
    # Check Service Health
    radarr_up = await check_service(settings.radarr.url, settings.radarr.api_key)
    sonarr_up = await check_service(settings.sonarr.url, settings.sonarr.api_key)
    
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
