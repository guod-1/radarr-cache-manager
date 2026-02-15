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
async def exclusions_page(request: Request):
    settings = get_user_settings()
    
    # Fetch tags to populate the dropdowns
    radarr_tags = []
    sonarr_tags = []
    try:
        radarr_tags = get_radarr_client().get_all_tags()
    except: pass
    try:
        sonarr_tags = get_sonarr_client().get_all_tags()
    except: pass

    return templates.TemplateResponse("exclusions.html", {
        "request": request,
        "user_settings": settings,
        "radarr_tags": radarr_tags,
        "sonarr_tags": sonarr_tags
    })

@router.post("/tags/add")
async def add_exclusion_tag(tag_id: int = Form(...)):
    settings = get_user_settings()
    if tag_id not in settings.exclusions.exclude_tag_ids:
        settings.exclusions.exclude_tag_ids.append(tag_id)
        save_user_settings(settings)
    return RedirectResponse(url="/exclusions/", status_code=303)

@router.post("/tags/remove")
async def remove_exclusion_tag(tag_id: int = Form(...)):
    settings = get_user_settings()
    if tag_id in settings.exclusions.exclude_tag_ids:
        settings.exclusions.exclude_tag_ids.remove(tag_id)
        save_user_settings(settings)
    return RedirectResponse(url="/exclusions/", status_code=303)

@router.post("/save")
async def save_exclusions(
    custom_folders: str = Form(""),
    plexcache_file_path: str = Form("/mnt/user/appdata/plexcache/plexcache")
):
    settings = get_user_settings()
    folder_list = [f.strip() for f in custom_folders.split("\n") if f.strip()]
    settings.exclusions.custom_folders = folder_list
    settings.exclusions.plexcache_file_path = plexcache_file_path
    save_user_settings(settings)
    return RedirectResponse(url="/exclusions/?success=true", status_code=303)
