"""
Dashboard Router

Main dashboard page showing overview and quick stats
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

from app.core.config import get_user_settings, get_settings
from app.services.exclusions import get_exclusion_manager
from app.core.scheduler import get_scheduler
from app.services.radarr import get_radarr_client

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    
    # Get various stats
    user_settings = get_user_settings()
    settings = get_settings()
    exclusion_manager = get_exclusion_manager()
    scheduler = get_scheduler()
    radarr_client = get_radarr_client()
    
    # Check Radarr connection
    radarr_connected = radarr_client.test_connection()
    
    # Get exclusion stats
    exclusion_stats = exclusion_manager.get_exclusion_stats()
    
    # Get scheduler info
    next_run = scheduler.get_next_run_time() if user_settings.scheduler.enabled else "Disabled"
    
    context = {
        "request": request,
        "radarr_connected": radarr_connected,
        "radarr_url": user_settings.radarr.url,
        "scheduler_enabled": user_settings.scheduler.enabled,
        "next_run": next_run,
        "exclusion_count": exclusion_stats['total'],
        "exclusion_files": exclusion_stats['files'],
        "exclusion_dirs": exclusion_stats['directories'],
        "tag_search_id": user_settings.tag_operation.search_tag_id,
        "tag_replace_id": user_settings.tag_operation.replace_tag_id,
        "custom_folder_count": len(user_settings.exclusions.custom_folders),
        "exclude_tag_count": len(user_settings.exclusions.exclude_tag_ids),
    }
    
    return templates.TemplateResponse("dashboard.html", context)


@router.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """API endpoint for dashboard stats (for HTMX updates)"""
    
    user_settings = get_user_settings()
    exclusion_manager = get_exclusion_manager()
    scheduler = get_scheduler()
    radarr_client = get_radarr_client()
    
    radarr_connected = radarr_client.test_connection()
    exclusion_stats = exclusion_manager.get_exclusion_stats()
    next_run = scheduler.get_next_run_time() if user_settings.scheduler.enabled else "Disabled"
    
    return {
        "radarr_connected": radarr_connected,
        "scheduler_enabled": user_settings.scheduler.enabled,
        "next_run": next_run,
        "exclusion_count": exclusion_stats['total'],
        "exclusion_files": exclusion_stats['files'],
        "exclusion_dirs": exclusion_stats['directories']
    }
