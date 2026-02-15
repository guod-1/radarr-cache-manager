"""
Operations Router

Handles running operations:
- Tag operations (find and replace tags)
- Exclusion builder (combine exclusion sources)
- Full operation (both)
"""

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse
import logging

from app.services.operations import run_tag_operation, run_exclusion_builder, run_full_operation

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/run/tags")
async def run_tags(background_tasks: BackgroundTasks):
    """Run tag operation only"""
    background_tasks.add_task(run_tag_operation)
    return {
        "success": True,
        "message": "Tag operation started"
    }


@router.post("/run/exclusions")
async def run_exclusions(background_tasks: BackgroundTasks):
    """Run exclusion builder only"""
    background_tasks.add_task(run_exclusion_builder)
    return {
        "success": True,
        "message": "Exclusion builder started"
    }


@router.post("/run/full")
async def run_full(background_tasks: BackgroundTasks):
    """Run both operations"""
    background_tasks.add_task(run_full_operation)
    return {
        "success": True,
        "message": "Full operation started"
    }


@router.post("/run")
async def run_operation(background_tasks: BackgroundTasks):
    """Run full operation (default)"""
    return await run_full(background_tasks)


@router.post("/run-sync/tags")
async def run_tags_sync():
    """Run tag operation synchronously"""
    try:
        result = run_tag_operation()
        return {
            "success": result['success'],
            "result": result
        }
    except Exception as e:
        logger.error(f"Tag operation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/run-sync/exclusions")
async def run_exclusions_sync():
    """Run exclusion builder synchronously"""
    try:
        result = run_exclusion_builder()
        return {
            "success": result['success'],
            "result": result
        }
    except Exception as e:
        logger.error(f"Exclusion builder failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
