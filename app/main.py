import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.routers import dashboard, movies, shows, exclusions, settings, logs, stats, operations, webhooks
from app.core.scheduler import scheduler_service
from app.core.config import get_user_settings

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/config/app.log"),
        logging.StreamHandler()
    ]
)

logging.getLogger("apscheduler").setLevel(logging.INFO)

from app.services.notifier import DiscordLogHandler
_discord_handler = DiscordLogHandler()
_discord_handler.setLevel(logging.WARNING)
logging.getLogger().addHandler(_discord_handler)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = FastAPI(title="Mover Tuning Exclusion Manager")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(movies.router, prefix="/movies", tags=["Movies"])
app.include_router(shows.router, prefix="/shows", tags=["Shows"])
app.include_router(exclusions.router, prefix="/exclusions", tags=["Exclusions"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(logs.router, prefix="/logs", tags=["Logs"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(operations.router, prefix="/operations", tags=["Operations"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])


@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")


@app.get("/health")
async def health():
    s = get_user_settings()
    config_path = "/config/settings.json"
    backup_path = "/config/settings.json.bak"

    state = {
        "radarr_url_set": bool(s.radarr.url),
        "radarr_key_set": bool(s.radarr.api_key),
        "sonarr_url_set": bool(s.sonarr.url),
        "sonarr_key_set": bool(s.sonarr.api_key),
        "radarr_tag_count": len(s.exclusions.radarr_exclude_tag_ids),
        "sonarr_tag_count": len(s.exclusions.sonarr_exclude_tag_ids),
        "full_sync_cron": s.exclusions.full_sync_cron,
        "log_monitor_cron": s.exclusions.log_monitor_cron,
        "last_build": s.exclusions.last_build,
        "last_stats_update": s.exclusions.last_stats_update,
    }

    healthy = all([state["radarr_url_set"], state["radarr_key_set"],
                   state["sonarr_url_set"], state["sonarr_key_set"]])

    return JSONResponse(
        status_code=200 if healthy else 500,
        content={
            "status": "ok" if healthy else "degraded — credentials missing",
            "config_file": {
                "exists": os.path.exists(config_path),
                "size_bytes": os.path.getsize(config_path) if os.path.exists(config_path) else 0,
                "backup_exists": os.path.exists(backup_path),
            },
            "settings": state,
        }
    )


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Mover Tuning Exclusion Manager — STARTING UP")
    logger.info("=" * 60)

    s = get_user_settings()
    logger.info(
        f"[STARTUP] radarr_url={s.radarr.url!r} "
        f"radarr_key={'SET' if s.radarr.api_key else '*** EMPTY ***'} "
        f"sonarr_url={s.sonarr.url!r} "
        f"sonarr_key={'SET' if s.sonarr.api_key else '*** EMPTY ***'}"
    )

    if not s.radarr.url or not s.radarr.api_key:
        logger.warning("[STARTUP] *** Radarr credentials missing — check /config/settings.json ***")
    if not s.sonarr.url or not s.sonarr.api_key:
        logger.warning("[STARTUP] *** Sonarr credentials missing — check /config/settings.json ***")

    scheduler_service.start()
    logger.info("[STARTUP] Scheduler initialized. Startup complete.")
