import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import get_user_settings, save_user_settings
from app.services.alert_log import get_alert_log
from app.services.webhook_handler import trigger_rebuild

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def webhooks_page(request: Request):
    settings = get_user_settings()
    alerts = get_alert_log().get_all()
    return templates.TemplateResponse("webhooks.html", {
        "request": request,
        "settings": settings,
        "alerts": alerts
    })


@router.post("/radarr")
async def radarr_webhook(request: Request):
    payload = await request.json()
    event = payload.get("eventType", "unknown")
    logger.info(f"[WEBHOOK] Radarr event: {event}")
    get_alert_log().add("info", "radarr", f"Radarr webhook received: {event}")
    trigger_rebuild("radarr")
    return {"status": "ok", "event": event}


@router.post("/sonarr")
async def sonarr_webhook(request: Request):
    payload = await request.json()
    event = payload.get("eventType", "unknown")
    logger.info(f"[WEBHOOK] Sonarr event: {event}")
    get_alert_log().add("info", "sonarr", f"Sonarr webhook received: {event}")
    trigger_rebuild("sonarr")
    return {"status": "ok", "event": event}


@router.post("/settings/save")
async def save_webhook_settings(request: Request):
    form = await request.form()
    settings = get_user_settings()
    settings.webhooks.enabled = form.get("enabled") == "on"
    cooldown = int(form.get("cooldown_seconds", 30))
    settings.webhooks.cooldown_seconds = max(30, min(300, cooldown))
    save_user_settings(settings)
    logger.info(f"[WEBHOOK] Settings saved — enabled={settings.webhooks.enabled} cooldown={settings.webhooks.cooldown_seconds}s")
    return RedirectResponse(url="/webhooks?status=saved", status_code=303)


@router.post("/notifications/save")
async def save_notification_settings(request: Request):
    form = await request.form()
    settings = get_user_settings()
    settings.webhooks.discord_webhook_url = form.get("discord_webhook_url", "").strip()
    settings.webhooks.discord_enabled = form.get("discord_enabled") == "on"
    settings.webhooks.discord_notify_warnings = form.get("discord_notify_warnings") == "on"
    save_user_settings(settings)
    logger.info(f"[WEBHOOK] Discord settings saved — enabled={settings.webhooks.discord_enabled}")
    return RedirectResponse(url="/webhooks?status=saved", status_code=303)


@router.post("/notifications/test")
async def test_notification():
    from app.services.notifier import send_discord_notification
    from app.core.config import get_user_settings
    settings = get_user_settings()
    if not settings.webhooks.discord_webhook_url:
        return RedirectResponse(url="/webhooks?status=no_url", status_code=303)
    send_discord_notification(
        settings.webhooks.discord_webhook_url,
        "success",
        "MTEM",
        "Test notification from Mover Tuning Exclusion Manager — everything is working!"
    )
    return RedirectResponse(url="/webhooks?status=test_sent", status_code=303)


@router.post("/alerts/clear")
async def clear_alerts():
    get_alert_log().clear()
    return RedirectResponse(url="/webhooks", status_code=303)
