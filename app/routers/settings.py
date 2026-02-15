"""
Settings Router - Complete rebuild with all endpoints
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import logging

from app.core.config import (
    get_user_settings, save_user_settings,
    RadarrSettings, SonarrSettings, RadarrTagOperation, SonarrTagOperation,
    ExclusionSettings, SchedulerSettings
)
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.core.scheduler import get_scheduler

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page"""
    user_settings = get_user_settings()
    radarr_client = get_radarr_client()
    sonarr_client = get_sonarr_client()
    
    radarr_tags = []
    sonarr_tags = []
    
    try:
        radarr_tags = radarr_client.get_all_tags()
    except Exception as e:
        logger.error(f"Failed to fetch Radarr tags: {e}")
    
    try:
        sonarr_tags = sonarr_client.get_all_tags()
    except Exception as e:
        logger.error(f"Failed to fetch Sonarr tags: {e}")
    
    context = {
        "request": request,
        "settings": user_settings,
        "tags": radarr_tags,
        "radarr_tags": radarr_tags,
        "sonarr_tags": sonarr_tags
    }
    
    return templates.TemplateResponse("settings.html", context)


@router.post("/radarr")
async def update_radarr(url: str = Form(...), api_key: str = Form(...)):
    user_settings = get_user_settings()
    user_settings.radarr = RadarrSettings(url=url, api_key=api_key)
    save_user_settings(user_settings)
    return RedirectResponse(url="/settings/?success=radarr", status_code=303)


@router.post("/radarr/test")
async def test_radarr():
    try:
        connected = get_radarr_client().test_connection()
        return {"success": connected, "message": "Connected!" if connected else "Failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/sonarr")
async def update_sonarr(url: str = Form(...), api_key: str = Form(...)):
    user_settings = get_user_settings()
    user_settings.sonarr = SonarrSettings(url=url, api_key=api_key)
    save_user_settings(user_settings)
    return RedirectResponse(url="/settings/?success=sonarr", status_code=303)


@router.post("/sonarr/test")
async def test_sonarr():
    try:
        connected = get_sonarr_client().test_connection()
        return {"success": connected, "message": "Connected!" if connected else "Failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/radarr-tags")
async def update_radarr_tags(
    radarr_search_tag_id: Optional[int] = Form(None),
    radarr_replace_tag_id: Optional[int] = Form(None)
):
    user_settings = get_user_settings()
    user_settings.radarr_tag_operation = RadarrTagOperation(
        search_tag_id=radarr_search_tag_id,
        replace_tag_id=radarr_replace_tag_id
    )
    save_user_settings(user_settings)
    logger.info(f"Radarr tags updated: search={radarr_search_tag_id}, replace={radarr_replace_tag_id}")
    return RedirectResponse(url="/settings/?success=radarr_tags", status_code=303)


@router.post("/sonarr-tags")
async def update_sonarr_tags(
    sonarr_search_tag_id: Optional[int] = Form(None),
    sonarr_replace_tag_id: Optional[int] = Form(None)
):
    user_settings = get_user_settings()
    user_settings.sonarr_tag_operation = SonarrTagOperation(
        search_tag_id=sonarr_search_tag_id,
        replace_tag_id=sonarr_replace_tag_id
    )
    save_user_settings(user_settings)
    logger.info(f"Sonarr tags updated: search={sonarr_search_tag_id}, replace={sonarr_replace_tag_id}")
    return RedirectResponse(url="/settings/?success=sonarr_tags", status_code=303)


@router.post("/scheduler")
async def update_scheduler(
    enabled: bool = Form(False),
    cron_expression: str = Form(...),
    ca_mover_check_cron: str = Form("30 23 * * *")
):
    user_settings = get_user_settings()
    user_settings.scheduler = SchedulerSettings(
        enabled=enabled,
        cron_expression=cron_expression,
        ca_mover_check_cron=ca_mover_check_cron
    )
    save_user_settings(user_settings)
    
    scheduler = get_scheduler()
    if enabled:
        scheduler.start()
    else:
        scheduler.stop()
    
    logger.info(f"Scheduler updated: enabled={enabled}")
    return RedirectResponse(url="/settings/?success=scheduler", status_code=303)
