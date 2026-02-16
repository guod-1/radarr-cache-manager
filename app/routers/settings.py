from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import get_user_settings, save_user_settings
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
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

@router.post("/radarr/save")
async def save_radarr(url: str = Form(...), api_key: str = Form(...)):
    settings = get_user_settings()
    settings.radarr.url = url
    settings.radarr.api_key = api_key
    status = "error"
    try:
        get_radarr_client().get_all_tags()
        status = "success"
    except Exception as e:
        logger.error(f"Radarr connection test failed: {e}")
    save_user_settings(settings)
    return RedirectResponse(url=f"/settings?radarr_status={status}", status_code=303)

@router.post("/sonarr/save")
async def save_sonarr(url: str = Form(...), api_key: str = Form(...)):
    settings = get_user_settings()
    settings.sonarr.url = url
    settings.sonarr.api_key = api_key
    status = "error"
    try:
        get_sonarr_client().get_all_tags()
        status = "success"
    except Exception as e:
        logger.error(f"Sonarr connection test failed: {e}")
    save_user_settings(settings)
    return RedirectResponse(url=f"/settings?sonarr_status={status}", status_code=303)

@router.post("/paths/save")
async def save_paths(movie_base_path: str = Form(...), tv_base_path: str = Form(...)):
    settings = get_user_settings()
    settings.exclusions.movie_base_path = movie_base_path
    settings.exclusions.tv_base_path = tv_base_path
    save_user_settings(settings)
    logger.info(f"Path normalization updated: {movie_base_path}, {tv_base_path}")
    return RedirectResponse(url="/settings?status=success", status_code=303)

@router.post("/automation/save")
async def save_automation(scheduler_enabled: bool = Form(False), cron_expression: str = Form(...)):
    settings = get_user_settings()
    settings.scheduler.enabled = scheduler_enabled
    settings.scheduler.cron_expression = cron_expression
    save_user_settings(settings)
    return RedirectResponse(url="/settings?automation_status=success", status_code=303)
