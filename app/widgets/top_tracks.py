import logging

from ..spotify_client import SpotifyError, spotify_request
from ._track_list import render_track_list

logger = logging.getLogger(__name__)

TRACK_LIMIT = 5
# Spotify has no true "weekly" window; short_term is its closest built-in
# approximation, covering roughly the last 4 weeks.
TIME_RANGE = "short_term"
TITLE = "Top Tracks (Last 4 Weeks)"


def _extract_artist(item):
    artists = item.get("artists", [])
    return artists[0].get("name", "") if artists else ""


def render(query_params):
    """Render the top-tracks widget; falls back to an empty list on error."""
    tracks = []
    try:
        data = spotify_request(f"me/top/tracks?time_range={TIME_RANGE}&limit={TRACK_LIMIT}")
        items = data.get("items", []) if data else []
        tracks = [
            {"song": item["name"], "artist": _extract_artist(item)}
            for item in items
            if item.get("name")
        ]
    except (SpotifyError, AttributeError, KeyError, TypeError):
        logger.warning("Spotify unavailable; serving an empty top-tracks widget")

    return render_track_list(query_params, TITLE, tracks)
