from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

from app.services.radarr import get_radarr_client

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def movies_page(request: Request):
    """Movies listing page - shows all movies from Radarr"""
    radarr_client = get_radarr_client()
    
    movies = []
    
    try:
        # Get all movies and tags from Radarr
        all_movies = radarr_client.get_all_movies()
        all_tags = radarr_client.get_all_tags()
        
        # Create tag ID to label mapping
        tag_map = {tag['id']: tag['label'] for tag in all_tags}
        
        for movie in all_movies:
            # Map tag IDs to tag labels
            tag_ids = movie.get('tags', [])
            tag_labels = [tag_map.get(tag_id, f"Unknown Tag {tag_id}") for tag_id in tag_ids]
            
            movies.append({
                'id': movie['id'],
                'title': movie['title'],
                'year': movie.get('year', 'N/A'),
                'tags': tag_labels
            })
    except Exception as e:
        logger.error(f"Failed to fetch movies: {e}")
    
    # Collect all unique tags across all movies for filter UI
    all_tag_labels = sorted(set(tag for m in movies for tag in m['tags']))

    context = {
        "request": request,
        "movies": movies,
        "total": len(movies),
        "all_tags": all_tag_labels
    }
    
    return templates.TemplateResponse("movies.html", context)
