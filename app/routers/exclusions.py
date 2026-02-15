from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import get_user_settings, save_user_settings, UserSettings
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.services.exclusions import get_exclusion_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def exclusions_page(request: Request, tab: str = "settings"):
    settings = get_user_settings()
    exclusion_manager = get_exclusion_manager()
    
    radarr_tags = []
    sonarr_tags = []
    try:
        radarr_tags = get_radarr_client().get_all_tags()
    except Exception: pass
    try:
        sonarr_tags = get_sonarr_client().get_all_tags()
    except Exception: pass

    stats = exclusion_manager.get_exclusion_stats()
    
    # Logic to fetch list of exclusions for the viewer tab
    exclusions_list = []
    if tab == "viewer":
        try:
            with open("/config/mover_exclusions.txt", "r") as f:
                exclusions_list = [line.strip() for line in f if line.strip()]
        except Exception: pass

    return templates.TemplateResponse("exclusions.html", {
        "request": request,
        "user_settings": settings, # Fixes the UndefinedError
        "radarr_tags": radarr_tags,
        "sonarr_tags": sonarr_tags,
        "tags": radarr_tags + sonarr_tags,
        "stats": stats,
        "total": stats.get('total_count', 0),
        "files": stats.get('total_count', 0),
        "directories": 0,
        "exclusions": exclusions_list,
        "active_tab": tab
    })

@router.post("/settings")
async def save_exclusion_settings(
    custom_folders: str = Form(""),
    exclude_tag_ids: str = Form(""),
    plexcache_file_path: str = Form("/mnt/user/appdata/plexcache/plexcache")
):
    settings = get_user_settings()
    
    # Update settings object
    settings.exclusions.custom_folders = [f.strip() for f in custom_folders.split('\n') if f.strip()]
    if exclude_tag_ids.strip():
        settings.exclusions.exclude_tag_ids = [int(t.strip()) for t in exclude_tag_ids.split(',') if t.strip().isdigit()]
    settings.exclusions.plexcache_file_path = plexcache_file_path
    
    save_user_settings(settings)
    return RedirectResponse(url="/exclusions/?success=true", status_code=303)

@router.post("/tags/add")
async def add_exclusion_tag(tag_id: int = Form(...)):
    settings = get_user_settings()
    if tag_id not in settings.exclusions.exclude_tag_ids:
        settings.exclusions.exclude_tag_ids.append(tag_id)
        save_user_settings(settings)
    return RedirectResponse(url="/exclusions/", status_code=303)
