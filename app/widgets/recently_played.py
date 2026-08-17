import logging

from ..spotify_client import SpotifyError, spotify_request
from ._track_list import render_track_list

logger = logging.getLogger(__name__)

TRACK_LIMIT = 5
TITLE = "Recently Played"


def _extract_artist(track):
    artists = track.get("artists", [])
    return artists[0].get("name", "") if artists else ""


def render(query_params):
    """Render the recently-played widget; falls back to an empty list on error."""
    tracks = []
    try:
        data = spotify_request(f"me/player/recently-played?limit={TRACK_LIMIT}")
        items = data.get("items", []) if data else []
        tracks = [
            {"song": entry["track"]["name"], "artist": _extract_artist(entry["track"])}
            for entry in items
            if entry.get("track", {}).get("name")
        ]
    except (SpotifyError, AttributeError, KeyError, TypeError):
        logger.warning("Spotify unavailable; serving an empty recently-played widget")

    return render_track_list(query_params, TITLE, tracks)
