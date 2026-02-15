from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import logging
from app.core.config import get_user_settings

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def logs_page(request: Request):
    """View the last 200 lines of the application log"""
    log_content = ""
    # Use the standard log path
    log_path = "/config/app.log"
    
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                lines = f.readlines()
                log_content = "".join(lines[-200:])
        except Exception as e:
            log_content = f"Error reading logs: {str(e)}"
    else:
        log_content = "Log file not found at /config/app.log"

    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": log_content
    })

@router.get("/download")
async def download_logs():
    """Download the full log file"""
    log_path = "/config/app.log"
    if os.path.exists(log_path):
        return FileResponse(log_path, filename="mover_manager.log")
    return {"error": "Log file not found"}
