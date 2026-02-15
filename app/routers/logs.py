"""
Logs Router

View and manage application logs
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
import logging
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Logs viewing page"""
    
    settings = get_settings()
    
    # Read last 1000 lines of log file
    log_lines = []
    try:
        if settings.log_file.exists():
            with open(settings.log_file, 'r') as f:
                all_lines = f.readlines()
                log_lines = all_lines[-1000:]  # Last 1000 lines
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
    
    context = {
        "request": request,
        "log_lines": log_lines,
        "log_file": str(settings.log_file)
    }
    
    return templates.TemplateResponse("logs.html", context)


@router.get("/api/tail")
async def tail_logs(lines: int = 100):
    """API endpoint to get last N lines of logs"""
    
    settings = get_settings()
    
    try:
        if settings.log_file.exists():
            with open(settings.log_file, 'r') as f:
                all_lines = f.readlines()
                log_lines = all_lines[-lines:]
                return {"success": True, "lines": log_lines}
        else:
            return {"success": False, "error": "Log file not found"}
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return {"success": False, "error": str(e)}


@router.get("/download", response_class=PlainTextResponse)
async def download_logs():
    """Download the full log file"""
    
    settings = get_settings()
    
    try:
        if settings.log_file.exists():
            with open(settings.log_file, 'r') as f:
                content = f.read()
            return PlainTextResponse(
                content=content,
                headers={"Content-Disposition": f"attachment; filename=radarr-cache-manager.log"}
            )
        else:
            return PlainTextResponse("Log file not found", status_code=404)
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return PlainTextResponse(f"Error: {str(e)}", status_code=500)
