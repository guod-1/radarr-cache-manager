from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import get_user_settings, save_user_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def exclusions_page(request: Request):
    settings = get_user_settings()
    return templates.TemplateResponse("exclusions.html", {
        "request": request,
        "user_settings": settings
    })

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
