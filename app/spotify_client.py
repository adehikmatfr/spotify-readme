from os import getenv
from time import monotonic

import requests

from .config import REQUEST_TIMEOUT, SPOTIFY_API_URL, TOKEN_CACHE_SECONDS, TOKEN_URL


class SpotifyError(Exception):
    """An expected error while communicating with Spotify."""


_cached_token = None
_cached_token_expires_at = 0


def get_token():
    """Return a cached access token or obtain a new one."""
    global _cached_token, _cached_token_expires_at

    if _cached_token and monotonic() < _cached_token_expires_at:
        return _cached_token

    client_id = getenv("CLIENT_ID")
    client_secret = getenv("CLIENT_SECRET")
    refresh_token = getenv("REFRESH_TOKEN")
    if not all((client_id, client_secret, refresh_token)):
        raise SpotifyError("Spotify credentials are not configured")

    try:
        response = requests.post(
            TOKEN_URL,
            auth=(client_id, client_secret),
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        _cached_token = payload["access_token"]
        _cached_token_expires_at = monotonic() + min(
            payload.get("expires_in", 3600), TOKEN_CACHE_SECONDS
        )
        return _cached_token
    except (requests.RequestException, ValueError, KeyError) as error:
        raise SpotifyError("Unable to obtain a Spotify access token") from error


def spotify_request(endpoint):
    """Make a request to Spotify without exposing upstream errors."""
    try:
        response = requests.get(
            f"{SPOTIFY_API_URL}/{endpoint}",
            headers={"Authorization": f"Bearer {get_token()}"},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 204:
            return {}
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as error:
        raise SpotifyError("Unable to read Spotify playback data") from error
