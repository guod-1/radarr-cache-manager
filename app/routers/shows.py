from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

from app.services.sonarr import get_sonarr_client

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def shows_page(request: Request):
    """Shows listing page - shows all TV shows from Sonarr"""
    sonarr_client = get_sonarr_client()
    
    shows = []
    
    try:
        # Get all series and tags from Sonarr
        all_series = sonarr_client.get_all_series()
        all_tags = sonarr_client.get_all_tags()
        
        # Create tag ID to label mapping
        tag_map = {tag['id']: tag['label'] for tag in all_tags}
        
        for series in all_series:
            # Map tag IDs to tag labels
            tag_ids = series.get('tags', [])
            tag_labels = [tag_map.get(tag_id, f"Unknown Tag {tag_id}") for tag_id in tag_ids]
            
            shows.append({
                'id': series['id'],
                'title': series['title'],
                'year': series.get('year', 'N/A'),
                'seasons': series.get('seasonCount', 0),
                'tags': tag_labels
            })
    except Exception as e:
        logger.error(f"Failed to fetch shows: {e}")
    
    all_tag_labels = sorted(set(tag for s in shows for tag in s['tags']))

    context = {
        "request": request,
        "shows": shows,
        "total": len(shows),
        "all_tags": all_tag_labels
    }
    
    return templates.TemplateResponse("shows.html", context)
