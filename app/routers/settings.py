"""
Settings Router
Handles all settings management
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
    
    # Get tags from both Radarr and Sonarr
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
        "radarr_tags": radarr_tags,
        "sonarr_tags": sonarr_tags,
        "tags": radarr_tags  # For backward compatibility with template
    }
    
    return templates.TemplateResponse("settings.html", context)


@router.post("/radarr")
async def update_radarr_settings(
    url: str = Form(...),
    api_key: str = Form(...)
):
    """Update Radarr settings"""
    user_settings = get_user_settings()
    
    user_settings.radarr = RadarrSettings(
        url=url,
        api_key=api_key
    )
    
    save_user_settings(user_settings)
    logger.info("Radarr settings updated")
    
    return RedirectResponse(url="/settings?success=radarr", status_code=303)


@router.post("/radarr/test")
async def test_radarr_connection():
    """Test Radarr connection"""
    radarr_client = get_radarr_client()
    
    try:
        connected = radarr_client.test_connection()
        if connected:
            return {"success": True, "message": "Connected to Radarr successfully!"}
        else:
            return {"success": False, "message": "Failed to connect to Radarr. Check URL and API key."}
    except Exception as e:
        logger.error(f"Radarr connection test failed: {e}")
        return {"success": False, "message": str(e)}


@router.post("/sonarr")
async def update_sonarr_settings(
    url: str = Form(...),
    api_key: str = Form(...)
):
    """Update Sonarr settings"""
    user_settings = get_user_settings()
    
    user_settings.sonarr = SonarrSettings(
        url=url,
        api_key=api_key
    )
    
    save_user_settings(user_settings)
    logger.info("Sonarr settings updated")
    
    return RedirectResponse(url="/settings?success=sonarr", status_code=303)


@router.post("/sonarr/test")
async def test_sonarr_connection():
    """Test Sonarr connection"""
    sonarr_client = get_sonarr_client()
    
    try:
        connected = sonarr_client.test_connection()
        if connected:
            return {"success": True, "message": "Connected to Sonarr successfully!"}
        else:
            return {"success": False, "message": "Failed to connect to Sonarr. Check URL and API key."}
    except Exception as e:
        logger.error(f"Sonarr connection test failed: {e}")
        return {"success": False, "message": str(e)}


@router.post("/radarr-tags")
async def update_radarr_tag_settings(
    radarr_search_tag_id: Optional[int] = Form(None),
    radarr_replace_tag_id: Optional[int] = Form(None)
):
    """Update Radarr tag operation settings"""
    user_settings = get_user_settings()
    
    user_settings.radarr_tag_operation = RadarrTagOperation(
        search_tag_id=radarr_search_tag_id,
        replace_tag_id=radarr_replace_tag_id
    )
    
    save_user_settings(user_settings)
    logger.info("Radarr tag settings updated")
    
    return RedirectResponse(url="/settings?success=radarr_tags", status_code=303)


@router.post("/sonarr-tags")
async def update_sonarr_tag_settings(
    sonarr_search_tag_id: Optional[int] = Form(None),
    sonarr_replace_tag_id: Optional[int] = Form(None)
):
    """Update Sonarr tag operation settings"""
    user_settings = get_user_settings()
    
    user_settings.sonarr_tag_operation = SonarrTagOperation(
        search_tag_id=sonarr_search_tag_id,
        replace_tag_id=sonarr_replace_tag_id
    )
    
    save_user_settings(user_settings)
    logger.info("Sonarr tag settings updated")
    
    return RedirectResponse(url="/settings?success=sonarr_tags", status_code=303)


@router.post("/scheduler")
async def update_scheduler_settings(
    enabled: bool = Form(False),
    cron_expression: str = Form(...),
    ca_mover_check_cron: str = Form("30 23 * * *")
):
    """Update scheduler settings"""
    user_settings = get_user_settings()
    
    user_settings.scheduler = SchedulerSettings(
        enabled=enabled,
        cron_expression=cron_expression,
        ca_mover_check_cron=ca_mover_check_cron
    )
    
    save_user_settings(user_settings)
    
    # Restart scheduler if enabled
    scheduler = get_scheduler()
    if enabled:
        scheduler.start()
    else:
        scheduler.stop()
    
    logger.info(f"Scheduler settings updated: enabled={enabled}")
    
    return RedirectResponse(url="/settings?success=scheduler", status_code=303)
