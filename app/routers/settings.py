Settings Router
Handles all settings management
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
import logging

from app.core.config import (
    get_user_settings, save_user_settings, UserSettings, 
    RadarrSettings, SonarrSettings, RadarrTagOperation, SonarrTagOperation,
    ExclusionSettings, SchedulerSettings
)
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.core.scheduler import get_scheduler

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


