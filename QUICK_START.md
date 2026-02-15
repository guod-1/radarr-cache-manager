# Quick Start Guide

## Prerequisites

- Docker installed
- Radarr running with API access
- Unraid mover exclusions setup
- Optional: PlexCache-D installed

## Installation

### Option 1: Docker Compose (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/radarr-cache-manager.git
cd radarr-cache-manager

# Update paths in docker-compose.yml to match your system
nano docker-compose.yml

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 2: Unraid (Production)

1. **Install from Community Applications**
   - Go to **Apps** tab
   - Search for "Radarr Cache Manager"
   - Click **Install**
   - Configure paths (see below)
   - Click **Apply**

2. **Or add manually:**
   - **Docker** tab → **Add Container**
   - **Repository:** `ghcr.io/yourusername/radarr-cache-manager:latest`
   - Configure paths and variables (see template)
   - Click **Apply**

### Option 3: Docker Run

```bash
docker run -d \
  --name radarr-cache-manager \
  -p 5858:5858 \
  -v /mnt/user/appdata/radarr-cache-manager:/config \
  -v /mnt/user/scripts:/scripts \
  -v /mnt/chloe:/mnt/chloe \
  -v /mnt/user/appdata/plexcache:/plexcache:ro \
  -e TZ=America/New_York \
  -e PUID=99 \
  -e PGID=100 \
  ghcr.io/yourusername/radarr-cache-manager:latest
```

## Initial Configuration

### 1. Access Web UI

Open: `http://your-server-ip:5858`

### 2. Configure Radarr Connection

Go to **Settings** → **Radarr Connection**

- **URL:** `http://192.168.1.100:7878` (your Radarr URL)
- **API Key:** Get from Radarr → Settings → General → Security → API Key
- **Source Tag ID:** The tag ID to process (default: 1)
- **Action:** `remove` (removes tag from high-rating movies)
- **High-Rating Tag ID:** Tag to add to high-rating movies (default: 41)

Click **Test Connection** to verify, then **Save**.

### 3. Set Rating Thresholds

Go to **Settings** → **Rating Thresholds**

Default values (movies must exceed ALL):
- IMDb: > 9.0
- TMDB: > 9.0  
- Metacritic: > 90
- Rotten Tomatoes: > 90

Adjust to your preference and click **Save**.

### 4. Configure Scheduler (Optional)

Go to **Settings** → **Scheduler**

- Check **Enable automatic runs**
- Set cron expression (default: `0 */6 * * *` = every 6 hours)
- Click **Save**

### 5. Run First Operation

Go to **Dashboard** → Click **Run Now**

Check **Logs** to monitor progress.

## Path Configuration

### Important Paths

**On Host:**
- `/mnt/user/appdata/radarr-cache-manager` → Container `/config`
- `/mnt/user/scripts` → Container `/scripts` (for mover_exclusions.txt)
- `/mnt/chloe` → Container `/mnt/chloe` (your cache drive)
- `/mnt/user/appdata/plexcache` → Container `/plexcache` (read-only)

**Generated Files:**
- `/mnt/user/scripts/mover_exclusions.txt` - Combined exclusions
- `/config/settings.json` - Application settings
- `/config/logs/radarr-cache-manager.log` - Application logs

## Workflow

1. **Script fetches movies** with Source Tag ID from Radarr
2. **Checks ratings** against thresholds (IMDb, TMDB, Metacritic, RT)
3. **High-rating movies:**
   - Removes source tag (or adds/replaces based on action)
   - Adds high-rating tag
   - Stays on cache drive
4. **Low-rating movies:**
   - File path added to exclusions
   - Can be moved to array by Unraid mover
5. **Combines exclusions** from:
   - Movies (this script)
   - PlexCache-D (if installed)
   - Folder exclusions
6. **Writes final** `mover_exclusions.txt`

## Verification

### Check Radarr Connection

Dashboard should show:
- ✅ **Radarr Status: Connected**

### Check Exclusions

Dashboard shows:
- **Total Exclusions:** X files, Y directories

### View Processed Movies

Go to **Movies** tab to see all movies with ratings and status.

### Monitor Logs

Go to **Logs** tab for real-time operation logs.

## Troubleshooting

### "Failed to connect to Radarr"
- Verify Radarr URL is correct
- Check API key is valid
- Ensure Radarr is accessible from container

### "No movies found"
- Verify Source Tag ID exists in Radarr
- Check that tag has movies assigned
- Review logs for API errors

### Exclusions file not created
- Check `/scripts` volume is mounted read/write
- Verify permissions (PUID/PGID)
- Check logs for errors

### Scheduler not running
- Verify scheduler is enabled in settings
- Check cron expression is valid
- View logs for scheduler messages

## Next Steps

- **Customize thresholds** to match your preferences
- **Set up scheduling** for automatic runs
- **Integrate with CA Mover Tuning** (Unraid plugin)
- **Monitor logs** for first few runs
- **Adjust tag IDs** as needed in Radarr

## Support

- **GitHub Issues:** https://github.com/yourusername/radarr-cache-manager/issues
- **Documentation:** See README.md for full details
