# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A serverless Flask app that renders three live Spotify widgets as SVG images (`/api` now-playing, `/api/top` top tracks, `/api/recent` recently played), meant to be embedded via `<img>` in a GitHub README. There is no frontend/build step.

## Commands

```bash
pip install -r api/requirements.txt   # install dependencies
python api/index.py                   # run locally at http://127.0.0.1:5000 (debug mode)
```

There is no test suite, linter, or build step configured in this repo.

Local development requires a `.env` file (loaded via `python-dotenv`) with `CLIENT_ID`, `CLIENT_SECRET`, and `REFRESH_TOKEN` — see the "Setup/Deployment" section of README.md for how to obtain them via Spotify's OAuth Authorization Code flow. The redirect URI used for that one-time flow (`http://127.0.0.1:8888/callback`) must be registered exactly in the Spotify app's dashboard settings, but no server needs to actually listen there — the code is read out of the browser's address bar after the redirect.

## Architecture

The code is split between a thin Vercel entrypoint and a Flask app package:

- `api/index.py` — the file Vercel actually deploys as a serverless function (auto-detected because it's `api/*.py`). It inserts the repo root onto `sys.path` (since Vercel/`python api/index.py` don't guarantee it's already there) and just calls `app.create_app()`. `vercel.json` rewrites all paths to this function; `api/requirements.txt` sits next to it because Vercel's Python builder looks for dependencies there.
- `app/__init__.py` — `create_app()`, the Flask app factory. Defines three routes — `/api/top`, `/api/recent`, and a catch-all (`/`, `/<path:path>`) for now-playing — each delegating to the matching `app/widgets/*.render(request.args)` and returning the SVG as `image/svg+xml` with `Cache-Control: public, s-maxage=60, stale-while-revalidate=300`.
- `app/config.py` — env loading (`load_dotenv`), constants (API URLs, cache durations), and the base64-inlined Spotify logo read from `app/assets/spotify_logo.txt`.
- `app/spotify_client.py` — `SpotifyError`, `get_token()` (caches the access token in module-level globals, capped at `TOKEN_CACHE_SECONDS`; exchanges `REFRESH_TOKEN` for a new one on expiry — the app only ever performs refresh-token grants at runtime, never the full authorization-code exchange), and `spotify_request()` (wraps calls to the Spotify Web API, translating all failures into `SpotifyError`).
- `app/theming.py` — resolves the `theme`, `bg`, and `bars` query params that all three widgets accept. `resolve_background()` validates `bg` against a strict hex-color regex before it's interpolated into a `<style>` block — this is the injection guard for user-controlled input reaching raw CSS in an endpoint that serves `image/svg+xml` (which browsers will execute as a live SVG/HTML document if opened directly, not just as an inert `<img>`).
- `app/widgets/now_playing.py` — `render()`, the now-playing widget and its fallback chain, the most complex of the three. It degrades through several levels, in order, so `/api` always returns a valid SVG and never leaks an upstream error:
  - `me/player/currently-playing` if something is actively playing (also carries `progress_ms`/`item.duration_ms`, rendered as the progress bar)
  - `me/player/recently-played?limit=1` if nothing is currently playing (no progress bar — that data isn't available here)
  - `_last_track`, a module-level global holding the last track that rendered successfully (survives gaps in playback within the same warm serverless instance)
  - `_last_successful_svg`, a cached full SVG string, reused if within `FALLBACK_CACHE_SECONDS` (note: this cache ignores query params, so during an outage a request with different `theme`/`bg`/`bars` than the last successful render will still get the old render's styling)
  - a neutral "Not listening right now" widget as the final fallback
  - Any `SpotifyError`/`AttributeError`/`IndexError`/`KeyError`/`TypeError` during this whole process is caught broadly and routed through the same fallback chain.
- `app/widgets/top_tracks.py` — `render()`, calls `me/top/tracks?time_range=short_term` (Spotify's closest approximation to "weekly"; needs the `user-top-read` OAuth scope, which the currently-configured `REFRESH_TOKEN` may not have — falls back to an empty list rather than erroring if the scope is missing).
- `app/widgets/recently_played.py` — `render()`, calls `me/player/recently-played?limit=5` and lists the results (no fallback state needed beyond an empty list).
- `app/widgets/_track_list.py` — shared rendering (`render_track_list()`) used by both `top_tracks.py` and `recently_played.py`, since they're visually identical list widgets that differ only in title and data source. Computes the SVG's height dynamically from the row count.
- Templates: `app/templates/now_playing.html` (SVG `foreignObject` with inline CSS, including the progress bar) and `app/templates/track_list.html` (shared by the two list widgets).

Note: since this runs on Vercel's serverless platform, module-level globals (`_cached_token` in `spotify_client.py`; `_last_track`/`_last_successful_svg` in `now_playing.py`) are per-instance and not guaranteed to persist across cold starts or be shared between concurrent instances.
