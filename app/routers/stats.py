from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.ca_mover import get_mover_parser
import re

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def parse_size_to_gb(size_str):
    """Helper to convert various size strings (GB, MB, KB) to a float in GB"""
    try:
        num = float(re.findall(r"[-+]?\d*\.\d+|\d+", size_str)[0])
        if 'TB' in size_str: return num * 1024
        if 'GB' in size_str: return num
        if 'MB' in size_str: return num / 1024
        if 'KB' in size_str: return num / (1024 * 1024)
        return 0
    except: return 0

@router.get("", response_class=HTMLResponse)
async def stats_page(request: Request):
    mover_parser = get_mover_parser()
    stats = mover_parser.get_latest_stats()
    
    # Calculate Total Size Protected
    total_gb = sum(parse_size_to_gb(f.get('size', '0')) for f in stats.get('protected_files', []))
    if total_gb > 1024:
        display_total = f"{round(total_gb/1024, 2)} TB"
    else:
        display_total = f"{round(total_gb, 2)} GB"

    return templates.TemplateResponse("stats.html", {
        "request": request,
        "stats": stats,
        "total_protected_size": display_total
    })
