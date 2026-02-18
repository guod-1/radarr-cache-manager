# Mover Tuning Exclusion Manager

A self-hosted Docker app for Unraid that automatically generates exclusion files for the [CA Mover Tuning](https://forums.unraid.net/topic/70783-plugin-ca-mover-tuning/) plugin — keeping your tagged media pinned to the cache drive and out of the array.

## What it does

CA Mover Tuning can skip moving specific files/folders by reading an exclusion list. Building and maintaining that list manually is tedious. This app automates it by:

- Querying **Radarr** and **Sonarr** for media tagged with your chosen "keep on cache" tags
- Reading **PlexCache-D** exclusion output (optional)
- Validating that each path actually exists on the cache drive
- Writing a clean exclusion file that CA Mover reads on each run

## Path Mappings

Radarr, Sonarr, and PlexCache store file paths using their own internal container mounts. These rarely match the actual path on your Unraid host. The **Path Mappings** table in Settings lets you define prefix rewrites applied before paths are written to the exclusion file.

| From (API returns) | To (written to exclusion file) |
|---|---|
| `/data/` | `/mnt/cache/data/` |
| `/chloe/` | `/mnt/cache/data/media/` |

The **Cache Mount Point** setting (`/mnt/cache` by default) is used separately for existence validation inside the container — it does not affect what gets written to the file.

## Setup

1. Add the container in Unraid Community Apps or manually via Docker
2. Map `/config`, `/plexcache` (optional), and your cache drive (e.g. `/mnt/cache`)
3. Open the UI and configure Radarr/Sonarr API credentials
4. Set your tags, path mappings, and schedule
5. Trigger a manual build or wait for the scheduler

## Container Paths

| Container Path | Purpose |
|---|---|
| `/config` | Persistent settings and output exclusion file |
| `/mnt/cache` | Cache drive mount for path validation |
| `/plexcache` | PlexCache-D output directory (optional) |
| `/mover_logs` | CA Mover Tuning log directory (optional) |

## Output

The exclusion file is written to `/config/mover_exclusions.txt`. Point CA Mover Tuning to this file in its plugin settings.

## Settings Reference

| Setting | Description |
|---|---|
| **Cache Mount Point** | Where your cache drive is mounted *inside this container* (e.g. `/mnt/cache`). Used only to check whether paths exist on cache before including them in the exclusion file. Never written to the output file. |
| **Path Mappings** | Prefix rewrites applied when writing paths to the exclusion file. Radarr/Sonarr/PlexCache store paths using their own internal mounts — use this to translate them to host-accessible paths. |
| **Mover Tuning Log Path** | Path to the CA Mover Tuning log file inside the container. Map your Unraid log directory here to enable mover activity monitoring and stats. |
| **Movie Base Path (Host)** | Root folder for movies on your cache drive as seen by the Unraid host. Used for display and stats only. |
| **TV Base Path (Host)** | Root folder for TV shows on your cache drive as seen by the Unraid host. Used for display and stats only. |
| **Exclusion Builder Schedule** | Cron expression controlling how often Radarr/Sonarr are queried and the exclusion file is rebuilt. |
| **Log Monitor Schedule** | Cron expression controlling how often the mover log is scanned to refresh stats. |
