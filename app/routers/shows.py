"""
Shows Router

Display TV shows from Sonarr with specific tags
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

from app.core.config import get_user_settings
from app.services.sonarr import get_sonarr_client

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def shows_page(request: Request):
    """Shows listing page"""
    
    user_settings = get_user_settings()
    sonarr_client = get_sonarr_client()
    
    shows = []
    tag_id = user_settings.tag_operation.search_tag_id
    
    if tag_id:
        try:
            # Get series with the tag
            series_ids = sonarr_client.get_series_ids_by_tag(tag_id)
            
            for series_id in series_ids:
                series = sonarr_client.get_series(series_id)
                if series:
                    shows.append({
                        'id': series['id'],
                        'title': series['title'],
                        'year': series.get('year', 'N/A'),
                        'path': series.get('path', ''),
                        'status': series.get('status', 'Unknown'),
                        'seasons': series.get('seasonCount', 0)
                    })
        except Exception as e:
            logger.error(f"Failed to fetch shows: {e}")
    
    context = {
        "request": request,
        "shows": shows,
        "tag_id": tag_id,
        "total": len(shows)
    }
    
    return templates.TemplateResponse("shows.html", context)
