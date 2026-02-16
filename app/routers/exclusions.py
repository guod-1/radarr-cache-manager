from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import get_user_settings, save_user_settings
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.services.exclusions import get_exclusion_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def exclusions_page(request: Request):
    user_settings = get_user_settings()
    radarr_client = get_radarr_client()
    sonarr_client = get_sonarr_client()
    
    tags, sonarr_tags = [], []
    try:
        tags = radarr_client.get_all_tags()
    except Exception: pass
    try:
        sonarr_tags = sonarr_client.get_all_tags()
    except Exception: pass
    
    excl_manager = get_exclusion_manager()
    stats = excl_manager.get_exclusion_stats()
    exclusions = excl_manager.get_all_exclusions()
    
    return templates.TemplateResponse("exclusions.html", {
        "request": request,
        "user_settings": user_settings,
        "tags": tags,
        "sonarr_tags": sonarr_tags,
        "stats": stats,
        "exclusions": exclusions
    })

@router.post("/radarr-tags/add")
async def add_radarr_tag(tag_id: int = Form(...)):
    user_settings = get_user_settings()
    if tag_id not in user_settings.exclusions.radarr_exclude_tag_ids:
        user_settings.exclusions.radarr_exclude_tag_ids.append(tag_id)
        save_user_settings(user_settings)
    return RedirectResponse(url="/exclusions/", status_code=303)

@router.post("/radarr-tags/remove")
async def remove_radarr_tag(tag_id: int = Form(...)):
    user_settings = get_user_settings()
    if tag_id in user_settings.exclusions.radarr_exclude_tag_ids:
        user_settings.exclusions.radarr_exclude_tag_ids.remove(tag_id)
        save_user_settings(user_settings)
    return RedirectResponse(url="/exclusions/", status_code=303)

@router.post("/sonarr-tags/add")
async def add_sonarr_tag(tag_id: int = Form(...)):
    user_settings = get_user_settings()
    if tag_id not in user_settings.exclusions.sonarr_exclude_tag_ids:
        user_settings.exclusions.sonarr_exclude_tag_ids.append(tag_id)
        save_user_settings(user_settings)
    return RedirectResponse(url="/exclusions/", status_code=303)

@router.post("/sonarr-tags/remove")
async def remove_sonarr_tag(tag_id: int = Form(...)):
    user_settings = get_user_settings()
    if tag_id in user_settings.exclusions.sonarr_exclude_tag_ids:
        user_settings.exclusions.sonarr_exclude_tag_ids.remove(tag_id)
        save_user_settings(user_settings)
    return RedirectResponse(url="/exclusions/", status_code=303)

@router.post("/plexcache")
async def save_plexcache(plexcache_file_path: str = Form(...)):
    user_settings = get_user_settings()
    user_settings.exclusions.plexcache_file_path = plexcache_file_path
    save_user_settings(user_settings)
    return RedirectResponse(url="/exclusions/?success=true", status_code=303)

@router.post("/custom-folders")
async def save_custom_folders(custom_folders: str = Form("")):
    folder_list = [f.strip() for f in custom_folders.split('\n') if f.strip()]
    user_settings = get_user_settings()
    user_settings.exclusions.custom_folders = folder_list
    save_user_settings(user_settings)
    return RedirectResponse(url="/exclusions/?success=true", status_code=303)
