"""
Movies Router

Display and manage movies
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

from app.services.radarr import get_radarr_client, MovieProcessor
from app.core.config import get_user_settings

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def movies_page(request: Request):
    """Movies listing page"""
    
    user_settings = get_user_settings()
    radarr_client = get_radarr_client()
    movie_processor = MovieProcessor()
    
    # Fetch movies with source tag
    try:
        movie_ids = radarr_client.get_movie_ids_by_tag(user_settings.radarr.source_tag_id)
        
        movies = []
        for movie_id in movie_ids[:50]:  # Limit to 50 for now
            try:
                movie = radarr_client.get_movie(movie_id)
                if movie:
                    ratings = movie_processor.get_movie_ratings(movie)
                    is_high = movie_processor.is_high_rating(ratings)
                    
                    movies.append({
                        'id': movie_id,
                        'title': movie.get('title', 'Unknown'),
                        'year': movie.get('year', ''),
                        'ratings': ratings,
                        'is_high_rating': is_high,
                        'tags': movie.get('tags', [])
                    })
            except Exception as e:
                logger.error(f"Error fetching movie {movie_id}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error fetching movies: {e}")
        movies = []
    
    context = {
        "request": request,
        "movies": movies,
        "thresholds": user_settings.thresholds.model_dump()
    }
    
    return templates.TemplateResponse("movies.html", context)


@router.get("/api/list")
async def get_movies_api():
    """API endpoint for movies list"""
    
    user_settings = get_user_settings()
    radarr_client = get_radarr_client()
    movie_processor = MovieProcessor()
    
    try:
        movie_ids = radarr_client.get_movie_ids_by_tag(user_settings.radarr.source_tag_id)
        
        movies = []
        for movie_id in movie_ids:
            try:
                movie = radarr_client.get_movie(movie_id)
                if movie:
                    ratings = movie_processor.get_movie_ratings(movie)
                    is_high = movie_processor.is_high_rating(ratings)
                    
                    movies.append({
                        'id': movie_id,
                        'title': movie.get('title', 'Unknown'),
                        'year': movie.get('year', ''),
                        'ratings': ratings,
                        'is_high_rating': is_high
                    })
            except:
                continue
        
        return {"success": True, "movies": movies}
    
    except Exception as e:
        logger.error(f"Error fetching movies: {e}")
        return {"success": False, "error": str(e)}
