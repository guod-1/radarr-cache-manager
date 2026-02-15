"""
Operations Router
Handles manual operations like tag operations and exclusion building
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


@router.post("/radarr-tags")
async def run_radarr_tags():
    """Run Radarr tag operation"""
    logger.info("Running Radarr tag operation...")
    result = run_radarr_tag_operation()
    return JSONResponse(content=result)


@router.post("/sonarr-tags")
async def run_sonarr_tags():
    """Run Sonarr tag operation"""
    logger.info("Running Sonarr tag operation...")
    result = run_sonarr_tag_operation()
    return JSONResponse(content=result)


@router.post("/build-exclusions")
async def build_exclusions():
    """Build exclusion file"""
    logger.info("Building exclusions...")
    result = run_exclusion_builder()
    return JSONResponse(content=result)


@router.post("/run-all")
async def run_all_operations():
    """Run all operations (Radarr tags + Sonarr tags + build exclusions)"""
    logger.info("Running all operations...")
    result = run_full_operation()
    return JSONResponse(content=result)
