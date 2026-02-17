from app.core.scheduler import scheduler_service
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import get_user_settings, save_user_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request):
    settings = get_user_settings()
    return templates.TemplateResponse("settings.html", {"request": request, "settings": settings})

@router.post("/paths/save")
async def save_paths(
    cache_mount_path: str = Form(...),
    movie_base_path: str = Form(...), 
    tv_base_path: str = Form(...),
    ca_mover_log_path: str = Form(...),
    full_sync_cron: str = Form(...),
    log_monitor_cron: str = Form(...)
):
    settings = get_user_settings()
    settings.exclusions.cache_mount_path = cache_mount_path
    settings.exclusions.movie_base_path = movie_base_path
    settings.exclusions.tv_base_path = tv_base_path
    settings.exclusions.ca_mover_log_path = ca_mover_log_path
    settings.exclusions.full_sync_cron = full_sync_cron
    settings.exclusions.log_monitor_cron = log_monitor_cron
    save_user_settings(settings)
    scheduler_service.reload_jobs()
    logger.info("System paths and schedules updated.")
    return RedirectResponse(url="/settings?status=success", status_code=303)

@router.post("/radarr/save")
async def save_radarr(url: str = Form(...), api_key: str = Form(...)):
    settings = get_user_settings()
    settings.radarr.url = url
    settings.radarr.api_key = api_key
    save_user_settings(settings)
    return RedirectResponse(url="/settings?radarr_status=success", status_code=303)

@router.post("/sonarr/save")
async def save_sonarr(url: str = Form(...), api_key: str = Form(...)):
    settings = get_user_settings()
    settings.sonarr.url = url
    settings.sonarr.api_key = api_key
    save_user_settings(settings)
    return RedirectResponse(url="/settings?sonarr_status=success", status_code=303)
