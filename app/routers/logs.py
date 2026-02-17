from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_log_data():
    log_path = "/config/app.log"
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                return "".join(f.readlines()[-200:])
        except: return "Error reading logs."
    return "Log file not found."

@router.get("", response_class=HTMLResponse)
async def logs_page(request: Request):
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "log_content": get_log_data()
    })

@router.get("/refresh", response_class=HTMLResponse)
async def refresh_logs(request: Request):
    # Returns only the raw log content for HTMX
    return HTMLResponse(content=get_log_data())

@router.get("/download")
async def download_logs():
    log_path = "/config/app.log"
    if os.path.exists(log_path):
        return FileResponse(log_path, filename="mover_manager.log")
    return {"error": "Log file not found"}
