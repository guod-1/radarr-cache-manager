from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import get_user_settings, save_user_settings
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.services.exclusions import get_exclusion_manager
import logging
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def exclusions_page(request: Request):
    """Exclusions management page"""
    user_settings = get_user_settings()
    
    # Get tags from both services
    radarr_client = get_radarr_client()
    sonarr_client = get_sonarr_client()
    
    tags = []
    sonarr_tags = []
    
    try:
        tags = radarr_client.get_all_tags()
    except Exception as e:
        logger.error(f"Failed to fetch Radarr tags: {e}")
    
    try:
        sonarr_tags = sonarr_client.get_all_tags()
    except Exception as e:
        logger.error(f"Failed to fetch Sonarr tags: {e}")
    
    # Get exclusion stats and content
    excl_manager = get_exclusion_manager()
    stats = excl_manager.get_exclusion_stats()
    exclusions = []
    
    try:
        with open("/config/mover_exclusions.txt", "r") as f:
            exclusions = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Failed to read exclusions file: {e}")
    
    context = {
        "request": request,
        "user_settings": user_settings,
        "tags": tags,
        "sonarr_tags": sonarr_tags,
        "stats": stats,
        "exclusions": exclusions
    }
    
    return templates.TemplateResponse("exclusions.html", context)


@router.post("/radarr-tags")
async def save_radarr_tags(radarr_exclude_tag_ids: List[int] = Form([])):
    """Save Radarr tag exclusions"""
    user_settings = get_user_settings()
    user_settings.exclusions.radarr_exclude_tag_ids = radarr_exclude_tag_ids
    save_user_settings(user_settings)
    logger.info(f"Radarr tags updated: {radarr_exclude_tag_ids}")
    return RedirectResponse(url="/exclusions/?success=true", status_code=303)


@router.post("/sonarr-tags")
async def save_sonarr_tags(sonarr_exclude_tag_ids: List[int] = Form([])):
    """Save Sonarr tag exclusions"""
    user_settings = get_user_settings()
    user_settings.exclusions.sonarr_exclude_tag_ids = sonarr_exclude_tag_ids
    save_user_settings(user_settings)
    logger.info(f"Sonarr tags updated: {sonarr_exclude_tag_ids}")
    return RedirectResponse(url="/exclusions/?success=true", status_code=303)


@router.post("/plexcache")
async def save_plexcache(plexcache_file_path: str = Form(...)):
    """Save PlexCache path"""
    user_settings = get_user_settings()
    user_settings.exclusions.plexcache_file_path = plexcache_file_path
    save_user_settings(user_settings)
    logger.info(f"PlexCache path updated: {plexcache_file_path}")
    return RedirectResponse(url="/exclusions/?success=true", status_code=303)


@router.post("/ca-mover")
async def save_ca_mover(ca_mover_log_path: str = Form(...)):
    """Save CA Mover log path"""
    user_settings = get_user_settings()
    user_settings.exclusions.ca_mover_log_path = ca_mover_log_path
    save_user_settings(user_settings)
    logger.info(f"CA Mover log path updated: {ca_mover_log_path}")
    return RedirectResponse(url="/exclusions/?success=true", status_code=303)


@router.post("/custom-folders")
async def save_custom_folders(custom_folders: str = Form("")):
    """Save custom folder exclusions"""
    folder_list = [f.strip() for f in custom_folders.split('\n') if f.strip()]
    user_settings = get_user_settings()
    user_settings.exclusions.custom_folders = folder_list
    save_user_settings(user_settings)
    logger.info(f"Custom folders updated: {len(folder_list)} folders")
    return RedirectResponse(url="/exclusions/?success=true", status_code=303)
