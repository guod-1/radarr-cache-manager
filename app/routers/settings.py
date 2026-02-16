from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import get_user_settings, save_user_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def settings_page(request: Request):
    settings = get_user_settings()
    return templates.TemplateResponse("settings.html", {"request": request, "settings": settings})

@router.post("/paths/save")
async def save_paths(movie_base_path: str = Form(...), tv_base_path: str = Form(...)):
    settings = get_user_settings()
    settings.exclusions.movie_base_path = movie_base_path
    settings.exclusions.tv_base_path = tv_base_path
    save_user_settings(settings)
    return RedirectResponse(url="/settings?status=success", status_code=303)

# ... include existing radarr/sonarr/automation save endpoints ...
