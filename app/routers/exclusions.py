"""
Exclusions Router
Manage exclusion settings and view exclusions
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
import logging

from app.core.config import get_user_settings, save_user_settings, ExclusionSettings
from app.services.exclusions import get_exclusion_manager
from app.services.radarr import get_radarr_client

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def exclusions_page(request: Request, tab: str = "settings"):
    """Exclusions page with tabs"""
    user_settings = get_user_settings()
    exclusion_manager = get_exclusion_manager()
    radarr_client = get_radarr_client()
    
    # Get tags
    tags = []
    try:
        tags = radarr_client.get_all_tags()
    except Exception as e:
        logger.error(f"Failed to fetch tags: {e}")
    
    # Get exclusion stats
    stats = exclusion_manager.get_exclusion_stats()
    
    # Get exclusions list for viewer tab
    exclusions = []
    if tab == "viewer":
        exclusions = exclusion_manager.get_all_exclusions()
    
    context = {
        "request": request,
        "user_settings": user_settings,
        "tags": tags,
        "stats": stats,
        "exclusions": exclusions,
        "active_tab": tab
    }
    
    return templates.TemplateResponse("exclusions.html", context)


@router.post("/settings")
async def save_exclusion_settings(
    custom_folders: str = Form(""),
    exclude_tag_ids: str = Form(""),
    plexcache_file_path: str = Form("/plexcache/unraid_mover_exclusions.txt"),
    ca_mover_log_path: str = Form("/config/ca.mover.tuning")
):
    """Save exclusion settings"""
    # Parse custom folders
    folder_list = [f.strip() for f in custom_folders.split('\n') if f.strip()]
    
    # Parse tag IDs
    tag_list = []
    if exclude_tag_ids.strip():
        tag_list = [int(t.strip()) for t in exclude_tag_ids.split(',') if t.strip().isdigit()]
    
    user_settings = get_user_settings()
    user_settings.exclusions = ExclusionSettings(
        custom_folders=folder_list,
        exclude_tag_ids=tag_list,
        plexcache_file_path=plexcache_file_path,
        ca_mover_log_path=ca_mover_log_path
    )
    
    save_user_settings(user_settings)
    logger.info("Exclusion settings saved")
    
    return RedirectResponse(url="/exclusions/?success=settings", status_code=303)


@router.post("/tags/add")
async def add_exclusion_tag(tag_id: int = Form(...)):
    """Add tag to exclusion list"""
    user_settings = get_user_settings()
    
    if tag_id not in user_settings.exclusions.exclude_tag_ids:
        user_settings.exclusions.exclude_tag_ids.append(tag_id)
        save_user_settings(user_settings)
        logger.info(f"Added tag {tag_id} to exclusions")
    
    return RedirectResponse(url="/exclusions/?success=tag_added", status_code=303)


@router.post("/tags/remove/{tag_id}")
async def remove_exclusion_tag(tag_id: int):
    """Remove tag from exclusion list"""
    user_settings = get_user_settings()
    
    if tag_id in user_settings.exclusions.exclude_tag_ids:
        user_settings.exclusions.exclude_tag_ids.remove(tag_id)
        save_user_settings(user_settings)
        logger.info(f"Removed tag {tag_id} from exclusions")
    
    return RedirectResponse(url="/exclusions/?success=tag_removed", status_code=303)


@router.get("/download")
async def download_exclusions():
    """Download mover_exclusions.txt file"""
    from app.core.config import get_settings
    settings = get_settings()
    exclusions_file = settings.config_dir / "mover_exclusions.txt"
    
    if exclusions_file.exists():
        return FileResponse(
            path=str(exclusions_file),
            filename="mover_exclusions.txt",
            media_type="text/plain"
        )
    else:
        return {"error": "Exclusions file not found"}


@router.post("/settings/save")
async def save_settings(
    custom_folders: str = Form(""),
    exclude_tag_ids: str = Form(""),
    plexcache_file_path: str = Form("/plexcache/unraid_mover_exclusions.txt"),
    ca_mover_log_path: str = Form("/config/ca.mover.tuning")
):
    """Alternative save endpoint"""
    return await save_exclusion_settings(
        custom_folders=custom_folders,
        exclude_tag_ids=exclude_tag_ids,
        plexcache_file_path=plexcache_file_path,
        ca_mover_log_path=ca_mover_log_path
    )
