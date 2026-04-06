# Agents

## Project Overview

**volco** is a companion web app for a Volumio media server. It provides:

- A FastAPI web UI for browsing and managing Volumio playlists
- A playlist updater (`refresh`) that discovers new NTS Radio tracks via the NTS API and adds them to Volumio playlists based on configurable keyword patterns
- HTML playlist pages generated and served statically

## Volumio Server

The Volumio media server runs on a local Raspberry Pi:

- **Host:** `volumio.local` (resolves to `192.168.2.22`)
- **SSH:** `ssh volumio@volumio.local`
- **Volumio API:** `http://volumio.local:3000` (Socket.IO + REST)
- **volco web UI:** `http://volumio.local:8080` (or wherever uvicorn is bound)
- **Hardware:** Raspberry Pi 3B+
- **App directory on server:** `/home/volumio/volco`

## Key Commands

### On the server (via SSH)

```bash
# Run the playlist refresh (fetches new NTS tracks, updates playlists, regenerates HTML)
ssh volumio@volumio.local "cd /home/volumio/volco && uv run refresh"

# Start the web server
ssh volumio@volumio.local "cd /home/volumio/volco && uv run uvicorn volco.app:app --host 0.0.0.0 --port 8080"

# Check logs
ssh volumio@volumio.local "tail -f /home/volumio/volco/logs/refresh.log"
```

### Local development

```bash
# Install dependencies
uv sync

# Run the web server locally (connects to volumio.local by default)
uvicorn volco.app:app --reload

# Run the refresh script locally (set VOLUMIO_URL if needed)
VOLUMIO_URL=volumio.local uv run refresh
```

## Architecture

- **`src/volco/app.py`** — FastAPI app: playlist UI, playback controls, pattern editor
- **`src/volco/updater.py`** — `refresh` entrypoint: discovers tracks, updates playlists, generates HTML
- **`src/volco/nts_client.py`** — NTS API client for fetching recent NTS Radio tracks
- **`src/volco/scraper.py`** — Volumio SoundCloud plugin browser (legacy track discovery)
- **`src/volco/controller.py`** — Volumio SocketIO controller (add/remove/list playlists)
- **`src/volco/constants.py`** — Paths and config (Volumio URL, playlist names, track sources)
- **`templates/`** — Jinja2 HTML templates
- **`static/playlists/`** — Generated playlist HTML pages served statically

## Deploying Changes

The server has git and uv. Deploy by pushing to the repo and pulling on the server:

```bash
# Push (requires personal SSH key — default key is rejected by GitHub)
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519-personal" git push -u origin main

# Pull latest, sync dependencies, and run refresh on the Pi
# Note: uv is at /home/volumio/.local/bin/uv (not on PATH in non-interactive SSH sessions)
ssh volumio@volumio.local "cd /home/volumio/volco && git pull && /home/volumio/.local/bin/uv sync && /home/volumio/.local/bin/uv run refresh"
```

## Notes

- The Volumio API runs on port 3000 (Socket.IO). The volco FastAPI app proxies playback commands to it so the browser only needs to talk to one port.
- Track discovery currently uses the NTS API (`find_candidate_tracks_nts`) rather than the Volumio SoundCloud plugin, which started returning 403s from the SoundCloud API.
- Playlist patterns are stored in `static/playlist_patterns.json` and edited via the `/patterns` UI route.
- `VOLUMIO_URL` env var defaults to `localhost` (for running on the server itself); set it to `volumio.local` when running locally.
