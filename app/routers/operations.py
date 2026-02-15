"""
Operations Router - Manual operations
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

from app.services.operations import (
    run_radarr_tag_operation,
    run_sonarr_tag_operation,
    run_exclusion_builder,
    run_full_operation
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run/radarr-tags")
async def run_radarr_tags():
    logger.info("Running Radarr tag operation...")
    result = run_radarr_tag_operation()
    return JSONResponse(content=result)


@router.post("/run/sonarr-tags")
async def run_sonarr_tags():
    logger.info("Running Sonarr tag operation...")
    result = run_sonarr_tag_operation()
    return JSONResponse(content=result)


@router.post("/run/exclusions")
async def run_exclusions():
    logger.info("Building exclusions...")
    result = run_exclusion_builder()
    return JSONResponse(content=result)


@router.post("/run/all")
async def run_all():
    logger.info("Running all operations...")
    result = run_full_operation()
    return JSONResponse(content=result)
