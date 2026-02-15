# Radarr Cache Manager

A Docker container with web UI for managing Radarr movie tags and generating Unraid mover exclusions.

## Overview

Radarr Cache Manager is a simple, flexible tool with two main functions:

### 1. Tag Manager
Search for movies with specific tags and optionally replace them with another tag.

**Use Cases:**
- Bulk tag operations
- Tag migration (e.g., replace old tags with new ones)
- Finding movies with specific tags

### 2. Exclusion Builder
Combine exclusions from multiple sources into a single `mover_exclusions.txt` file.

**Sources:**
- Custom folder paths (added via UI)
- Movies with specific tags (select tags to exclude)
- PlexCache-D exclusions file (auto-combined with path conversion)

**Features:**
- Automatic path conversion for PlexCache-D (`/chloe/` → `/mnt/chloe/data/media/`)
- Filters redundant entries (files when parent directory is excluded)
- Web UI for easy configuration
- Scheduled automatic runs

## Quick Start

### Docker Compose

```yaml
version: '3.8'
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

### First Run Setup

1. **Access Web UI:** `http://your-server-ip:5858`

2. **Configure Radarr Connection:**
   - Go to Settings → Radarr Connection
   - Enter your Radarr URL and API key
   - Click "Test Connection"
   - Click "Save"

3. **Configure Tag Operations (Optional):**
   - Go to Settings → Tag Operation
   - Select a tag to search for
   - Optionally select a tag to replace it with
   - Click "Save"

4. **Configure Exclusion Builder:**
   - Go to Settings → Exclusion Settings
   - Add custom folder paths (one per line)
   - Select tags whose movies should be excluded
   - Set PlexCache-D file path (default: `/plexcache/unraid_mover_exclusions.txt`)
   - Click "Save"

5. **Run Operations:**
   - Go to Dashboard
   - Click "Run Tags" (tag operation only)
   - Click "Build Exclusions" (exclusion builder only)
   - Click "Run All" (both operations)

## Operations

### Tag Operation

**What it does:**
1. Connects to Radarr
2. Fetches all movies with the "search tag"
3. Optionally replaces the tag with the "replace tag"

**When to use:**
- Bulk tag changes
- Tag cleanup
- Finding movies with specific tags

**To skip:** Leave "Search for Tag ID" empty in settings.

### Exclusion Builder

**What it does:**
1. Starts with custom folders you specified
2. Adds movies that have any of the selected "exclude tags"
3. Combines PlexCache-D exclusions (with path conversion)
4. Filters out redundant entries
5. Writes final `mover_exclusions.txt`

**Path Conversion:**
PlexCache-D uses container paths like `/chloe/movies/`. This tool automatically converts them to host paths like `/mnt/chloe/data/media/movies/`.

## Configuration

### Tag Operation Settings

- **Search for Tag ID:** Movies with this tag will be found
- **Replace with Tag ID:** Optional - replace search tag with this tag
- Leave both empty to skip tag operations entirely

### Exclusion Settings

- **Custom Folders:** Add any folder paths you want always excluded (one per line)
- **Exclude Movies with Tags:** Select tags - movies with these tags will be added to exclusions
- **PlexCache-D File Path:** Path to PlexCache-D's `unraid_mover_exclusions.txt` file

### Scheduler

- **Enable automatic runs:** Check to enable
- **Cron Expression:** When to run (default: `0 */6 * * *` = every 6 hours)

## File Outputs

- `/mnt/user/scripts/mover_exclusions.txt` - Combined exclusions for Unraid mover
- `/config/settings.json` - Application settings
- `/config/logs/radarr-cache-manager.log` - Application logs

## Use Cases

### Example 1: Keep Favorites on Cache

**Goal:** Keep movies tagged "favorites" on cache drive

**Setup:**
1. Tag your favorite movies in Radarr with tag ID 5
2. In Exclusion Settings, select tag 5 in "Exclude Movies with Tags"
3. Run "Build Exclusions"
4. Result: All favorite movies are added to mover exclusions

### Example 2: Tag Migration

**Goal:** Replace old "cache" tag (ID 1) with new "keep" tag (ID 10)

**Setup:**
1. In Tag Operation, set "Search for Tag ID" = 1
2. Set "Replace with Tag ID" = 10
3. Run "Run Tags"
4. Result: All movies with tag 1 now have tag 10 instead

### Example 3: Combine with PlexCache-D

**Goal:** Combine PlexCache-D cached files with custom exclusions

**Setup:**
1. Set PlexCache-D file path to `/plexcache/unraid_mover_exclusions.txt`
2. Add custom folders (e.g., `/mnt/chloe/data/media/movies/Kids/`)
3. Run "Build Exclusions"
4. Result: One file with PlexCache files + your custom folders

## Troubleshooting

### "Failed to connect to Radarr"
- Check Radarr URL is correct
- Verify API key is valid
- Ensure Radarr is accessible from container

### "No movies found"
- Verify the tag ID exists in Radarr
- Check that tag has movies assigned

### Exclusions file not created
- Check `/scripts` volume is mounted read/write
- Verify permissions (PUID/PGID)
- Check logs for errors

## Architecture

```
┌─────────────────────────────────┐
│      Web UI (Port 5858)          │
│   Dashboard | Settings | Logs    │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│       FastAPI Backend            │
│  ┌──────────┐  ┌──────────┐    │
│  │ Radarr   │  │ Exclusion │    │
│  │ Client   │  │ Manager   │    │
│  └──────────┘  └──────────┘    │
└──────────────────────────────────┘
```

## License

MIT License
