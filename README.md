# Mover Tuning Exclusion Manager (MTEM) v2.0

![Project Icon](logo.png)

MTEM is a specialized automation tool designed for **Unraid** users. It bridges the gap between your media services (Radarr/Sonarr) and the **CA Mover Tuning** plugin by dynamically managing your mover exclusion list.

## 🚀 Key Features in v2.0
* **Dual-Cron Automation**: Independent scheduling for the Exclusion Builder and the Log Monitor.
* **Dynamic Exclusion Generation**: Automatically scans your Radarr/Sonarr libraries to ensure files currently being seeded or accessed aren't moved prematurely from the cache.
* **Real-Time Dashboard**: Monitor your cache health, protected file counts, and mover logs through a sleek, modern web interface.
* **Seamless Integration**: Designed to output the standard `unraid_mover_exclusions.txt` format used by the CA Mover Tuning plugin.

## 🛠️ Installation & Setup

1.  **Docker Deployment**: Deploy the container pointing to your script directory.
2.  **Service Links**: Input your Radarr/Sonarr URLs and API keys in the **Settings** tab.
3.  **Configure Schedules**:
    * **Exclusion Builder**: Set how often the script rebuilds your exclusion list (e.g., `0 * * * *` for hourly).
    * **Log Monitor**: Set how often the dashboard refreshes its mover statistics (e.g., `*/5 * * * *` for every 5 minutes).

## 📂 Configuration Paths
* **Cache Mount**: Typically `/mnt/cache`
* **Exclusion File**: `/plexcache/unraid_mover_exclusions.txt`
* **Mover Logs**: Path to your `ca.mover.tuning.log`

---
*Developed for the Unraid community to optimize SSD cache lifespan and media availability.*
