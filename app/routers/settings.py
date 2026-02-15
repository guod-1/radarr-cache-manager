from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import get_user_settings, save_user_settings, UserSettings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def settings_page(request: Request):
    settings = get_user_settings()
    return templates.TemplateResponse("settings.html", {
        "request": request, 
        "settings": settings
    })

@router.post("/save")
async def save_settings(
    radarr_url: str = Form(...),
    radarr_key: str = Form(...),
    sonarr_url: str = Form(...),
    sonarr_key: str = Form(...),
    scheduler_enabled: bool = Form(False),
    cron_expression: str = Form("0 */6 * * *")
):
    settings = get_user_settings()
    
    # Update Radarr/Sonarr while preserving last_sync timestamps
    settings.radarr.url = radarr_url
    settings.radarr.api_key = radarr_key
    settings.sonarr.url = sonarr_url
    settings.sonarr.api_key = sonarr_key
    
    # Update Scheduler
    settings.scheduler.enabled = scheduler_enabled
    settings.scheduler.cron_expression = cron_expression
    
    save_user_settings(settings)
    return RedirectResponse(url="/settings?success=true", status_code=303)
