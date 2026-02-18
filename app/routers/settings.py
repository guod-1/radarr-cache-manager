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
    request: Request,
    cache_mount_path: str = Form(...),
    movie_base_path: str = Form(...),
    tv_base_path: str = Form(...),
    ca_mover_log_path: str = Form(...),
    full_sync_cron: str = Form(...),
    log_monitor_cron: str = Form(...)
):
    from app.core.config import ServicePathMapping
    settings = get_user_settings()
    settings.exclusions.cache_mount_path = cache_mount_path
    settings.exclusions.movie_base_path = movie_base_path
    settings.exclusions.tv_base_path = tv_base_path
    settings.exclusions.ca_mover_log_path = ca_mover_log_path
    settings.exclusions.full_sync_cron = full_sync_cron
    settings.exclusions.log_monitor_cron = log_monitor_cron

    form_data = await request.form()
    settings.exclusions.radarr_mapping = ServicePathMapping(
        from_prefix=form_data.get("radarr_from", "").strip(),
        to_prefix=form_data.get("radarr_to", "").strip()
    )
    settings.exclusions.sonarr_mapping = ServicePathMapping(
        from_prefix=form_data.get("sonarr_from", "").strip(),
        to_prefix=form_data.get("sonarr_to", "").strip()
    )
    settings.exclusions.plexcache_mapping = ServicePathMapping(
        from_prefix=form_data.get("plexcache_from", "").strip(),
        to_prefix=form_data.get("plexcache_to", "").strip()
    )

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
    try:
        from app.services.radarr import get_radarr_client
        get_radarr_client().get_all_movies()
        return RedirectResponse(url="/settings?radarr_status=success", status_code=303)
    except Exception:
        return RedirectResponse(url="/settings?radarr_status=error", status_code=303)

@router.post("/sonarr/save")
async def save_sonarr(url: str = Form(...), api_key: str = Form(...)):
    settings = get_user_settings()
    settings.sonarr.url = url
    settings.sonarr.api_key = api_key
    save_user_settings(settings)
    try:
        from app.services.sonarr import get_sonarr_client
        get_sonarr_client().get_all_series()
        return RedirectResponse(url="/settings?sonarr_status=success", status_code=303)
    except Exception:
        return RedirectResponse(url="/settings?sonarr_status=error", status_code=303)

@router.get("/path-prefixes")
async def get_path_prefixes():
    """Detect path prefixes from Radarr, Sonarr, and PlexCache"""
    from app.services.radarr import get_radarr_client
    from app.services.sonarr import get_sonarr_client
    from pathlib import Path
    results = {}
    try:
        movies = get_radarr_client().get_all_movies()
        for m in movies:
            p = (m.get('movieFile', {}) or {}).get('path') or m.get('path', '')
            if p:
                parts = p.lstrip('/').split('/')
                results['Radarr'] = '/' + parts[0] + '/'
                break
    except Exception as e:
        results['Radarr'] = f"Error: {e}"
    try:
        shows = get_sonarr_client().get_all_series()
        for s in shows:
            p = s.get('path', '')
            if p:
                parts = p.lstrip('/').split('/')
                results['Sonarr'] = '/' + parts[0] + '/'
                break
    except Exception as e:
        results['Sonarr'] = f"Error: {e}"
    try:
        settings = get_user_settings()
        pc = Path(settings.exclusions.plexcache_file_path)
        if pc.exists():
            with open(pc) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.lstrip('/').split('/')
                        results['Plexcache'] = '/' + parts[0] + '/'
                        break
    except Exception as e:
        results['Plexcache'] = f"Error: {e}"
    return results
