import logging
from datetime import datetime
from app.services.exclusions import get_exclusion_manager
from app.services.radarr import get_radarr_client
from app.services.sonarr import get_sonarr_client
from app.core.config import get_user_settings, save_user_settings

logger = logging.getLogger(__name__)

def _update_last_run(field: str):
    try:
        settings = get_user_settings()
        setattr(settings.last_run, field, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        save_user_settings(settings)
    except Exception as e:
        logger.error(f"Failed to update last run time for {field}: {e}")

async def run_exclusion_builder():
    try:
        manager = get_exclusion_manager()
        count = manager.combine_exclusions()
        _update_last_run("exclusion")
        return {"status": "success", "message": f"Combined {count} exclusions"}
    except Exception as e:
        logger.error(f"Exclusion builder failed: {e}")
        return {"status": "error", "message": str(e)}

async def run_radarr_tag_operation():
    try:
        settings = get_user_settings()
        ops = settings.radarr_tag_operation
        if not ops or ops.search_tag_id is None or ops.replace_tag_id is None:
            return {"status": "skipped", "message": "Radarr tags not configured"}
        client = get_radarr_client()
        movies = client.get_all_movies()
        affected = 0
        for movie in movies:
            tags = movie.get('tags', [])
            if ops.search_tag_id in tags:
                new_tags = [t for t in tags if t != ops.search_tag_id]
                if ops.replace_tag_id not in new_tags:
                    new_tags.append(ops.replace_tag_id)
                movie['tags'] = new_tags
                client.update_movie(movie)
                affected += 1
        
        _update_last_run("radarr")
        return {"status": "success", "message": f"Updated {affected} movies"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def run_sonarr_tag_operation():
    try:
        settings = get_user_settings()
        ops = settings.sonarr_tag_operation
        if not ops or ops.search_tag_id is None or ops.replace_tag_id is None:
            return {"status": "skipped", "message": "Sonarr tags not configured"}
        client = get_sonarr_client()
        shows = client.get_all_shows()
        affected = 0
        for show in shows:
            tags = show.get('tags', [])
            if ops.search_tag_id in tags:
                new_tags = [t for t in tags if t != ops.search_tag_id]
                if ops.replace_tag_id not in new_tags:
                    new_tags.append(ops.replace_tag_id)
                show['tags'] = new_tags
                client.update_show(show)
                affected += 1
        
        _update_last_run("sonarr")
        return {"status": "success", "message": f"Updated {affected} shows"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def run_full_sync():
    try:
        await run_radarr_tag_operation()
        await run_sonarr_tag_operation()
        res = await run_exclusion_builder()
        return {"status": "success", "message": f"Full sync complete. {res.get('message', '')}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
