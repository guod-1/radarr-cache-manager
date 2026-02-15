# Radarr Cache Manager

A Docker container with web UI for managing Radarr movie caching and Unraid mover exclusions based on movie ratings.

## Overview

Radarr Cache Manager automates the process of keeping highly-rated movies on your Unraid cache drive while allowing lower-rated content to be moved to the array. It integrates with Radarr, PlexCache-D, and the Unraid mover system.

### What It Does

1. **Fetches movies from Radarr** with a specific tag
2. **Analyzes ratings** from IMDb, TMDB, Metacritic, and Rotten Tomatoes
3. **Manages tags** - removes/adds tags based on rating thresholds
4. **Generates exclusion lists** - creates mover_exclusions.txt for Unraid
5. **Integrates with PlexCache-D** - combines exclusions from multiple sources
6. **Filters redundantly** - removes unnecessary entries (files in excluded directories)

### Use Case

- Keep highly-rated movies permanently on cache (fast SSD access)
- Allow lower-rated movies to move to array (save cache space)
- Work seamlessly with PlexCache-D for comprehensive cache management
- Automate the entire process with scheduling

## Features

- 🎨 **Modern Web UI** - Clean dashboard with real-time updates
- ⚙️ **Easy Configuration** - Change settings via web interface
- 📊 **Movie Browser** - View all movies with ratings and cache status
- 📅 **Scheduling** - Automatic runs with cron expressions
- 📝 **Live Logs** - Real-time log viewer with filtering
- 🔔 **Unraid Notifications** - Native notification support
- 🐳 **Docker Ready** - Simple installation on Unraid

## Quick Start

### Docker Run

```bash
docker run -d \
  --name radarr-cache-manager \
  -p 5858:5858 \
  -v /mnt/user/appdata/radarr-cache-manager:/config \
  -v /mnt/user/scripts:/scripts \
  -v /mnt/chloe:/mnt/chloe \
  -v /mnt/user/appdata/plexcache:/plexcache:ro \
  -e TZ=America/New_York \
  ghcr.io/yourusername/radarr-cache-manager:latest
```

### Docker Compose

```yaml
version: '3'
services:
  radarr-cache-manager:
    image: ghcr.io/yourusername/radarr-cache-manager:latest
    container_name: radarr-cache-manager
    ports:
      - "5858:5858"
    volumes:
      - /mnt/user/appdata/radarr-cache-manager:/config
      - /mnt/user/scripts:/scripts
      - /mnt/chloe:/mnt/chloe
      - /mnt/user/appdata/plexcache:/plexcache:ro
    environment:
      - TZ=America/New_York
      - PUID=99
      - PGID=100
    restart: unless-stopped
```

### Unraid Installation

1. Go to **Docker** → **Add Container**
2. Search Community Applications for "Radarr Cache Manager"
3. Click **Install**
4. Configure paths and click **Apply**

## Configuration

### First Run

1. Open `http://your-server-ip:5858`
2. Go to **Settings**
3. Configure Radarr connection (URL + API key)
4. Set rating thresholds
5. Configure tag IDs
6. Set up schedule (optional)
7. Click **Test Connection**
8. Click **Save**

### Rating Thresholds

Default settings for "high-rating" movies:
- IMDb > 9.0
- TMDB > 9.0
- Metacritic > 90
- Rotten Tomatoes > 90

All thresholds must be met for a movie to be considered high-rating.

### Tag Configuration

- **Source Tag ID**: Movies with this tag are processed (default: 1)
- **Action**: add, remove, or replace tags
- **High-Rating Tag ID**: Tag added to high-rating movies (default: 41)

### Path Mappings

Configure how paths are translated between systems:
- **Plex Path**: Path as Plex sees it (e.g., `/data/media/movies/`)
- **Host Path**: Actual path on Unraid (e.g., `/mnt/chloe/data/media/movies/`)

## Requirements

- Radarr v3+ with API access
- Unraid 6.9+ (for mover exclusions)
- Optional: PlexCache-D for enhanced cache management

## Architecture

```
┌─────────────────────────────────────────┐
│         Web UI (Port 5858)              │
│  Dashboard | Settings | Movies | Logs   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         FastAPI Backend                  │
│  ┌──────────┐  ┌──────────┐            │
│  │ Radarr   │  │ Scheduler │            │
│  │ Client   │  │ (APScheduler)          │
│  └──────────┘  └──────────┘            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          File Operations                 │
│  • Generate exclusions                   │
│  • Combine sources (PlexCache, folders) │
│  • Filter redundant entries              │
│  • Update mover_exclusions.txt          │
└──────────────────────────────────────────┘
```

## File Outputs

- `/scripts/mover_exclusions.txt` - Combined exclusions for Unraid mover
- `/config/settings.json` - Application settings
- `/config/logs/` - Application logs
- `/config/data.db` - SQLite database (run history, movie cache)

## Troubleshooting

### Can't connect to Radarr
- Verify Radarr URL is correct (include http:// or https://)
- Check API key is valid
- Ensure Radarr is accessible from the container

### Exclusions file not updating
- Check logs for errors
- Verify `/scripts` volume is mounted read/write
- Ensure PlexCache paths are correct

### No movies found
- Verify TAG_ID exists in Radarr and has movies
- Check that movies have ratings data
- Review logs for API errors

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [HTMX](https://htmx.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- Inspired by [PlexCache-D](https://github.com/StudioNirin/PlexCache-D)
