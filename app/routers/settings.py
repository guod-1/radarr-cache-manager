"""
Settings Router

Handles all settings management
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
import logging

from app.core.config import (
    get_user_settings, save_user_settings, UserSettings, 
    RadarrSettings, TagOperation, ExclusionSettings, SchedulerSettings
)
from app.services.radarr import get_radarr_client
from app.core.scheduler import get_scheduler

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page"""
    user_settings = get_user_settings()
    radarr_client = get_radarr_client()
    
    # Get available tags from Radarr
    tags = []
    try:
        if user_settings.radarr.api_key:
            tags = radarr_client.get_all_tags()
    except Exception as e:
        logger.error(f"Failed to fetch tags: {e}")
    
    context = {
        "request": request,
        "settings": user_settings,
        "tags": tags
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


@router.post("/tags")
async def update_tag_settings(
    search_tag_id: Optional[str] = Form(None),
    replace_tag_id: Optional[str] = Form(None)
):
    """Update tag operation settings"""
    user_settings = get_user_settings()
    
    # Convert empty strings to None, otherwise to int
    search_id = int(search_tag_id) if search_tag_id and search_tag_id != "" else None
    replace_id = int(replace_tag_id) if replace_tag_id and replace_tag_id != "" else None
    
    user_settings.tag_operation = TagOperation(
        search_tag_id=search_id,
        replace_tag_id=replace_id
    )
    
    save_user_settings(user_settings)
    logger.info(f"Tag settings updated: search={search_id}, replace={replace_id}")
    
    return RedirectResponse(url="/settings?success=tags", status_code=303)


@router.post("/exclusions")
async def update_exclusion_settings(
    custom_folders: str = Form(""),
    exclude_tag_ids: List[str] = Form([]),
    plexcache_file_path: str = Form(...)
):
    """Update exclusion settings"""
    user_settings = get_user_settings()
    
    # Parse custom folders (one per line)
    folders = [f.strip() for f in custom_folders.split('\n') if f.strip()]
    
    # Convert tag IDs to integers
    tag_ids = [int(tid) for tid in exclude_tag_ids if tid]
    
    user_settings.exclusions = ExclusionSettings(
        custom_folders=folders,
        exclude_tag_ids=tag_ids,
        plexcache_file_path=plexcache_file_path
    )
    
    save_user_settings(user_settings)
    logger.info(f"Exclusion settings updated: {len(folders)} folders, {len(tag_ids)} tags")
    
    return RedirectResponse(url="/settings?success=exclusions", status_code=303)


@router.post("/scheduler")
async def update_scheduler(
    enabled: bool = Form(False),
    cron_expression: str = Form(...)
):
    """Update scheduler settings"""
    user_settings = get_user_settings()
    
    user_settings.scheduler = SchedulerSettings(
        enabled=enabled,
        cron_expression=cron_expression
    )
    
    save_user_settings(user_settings)
    logger.info(f"Scheduler settings updated: enabled={enabled}, cron={cron_expression}")
    
    # Update the actual scheduler
    scheduler = get_scheduler()
    scheduler.update_schedule()
    
    return RedirectResponse(url="/settings?success=scheduler", status_code=303)
