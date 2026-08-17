import logging
from random import randint
from time import monotonic

from flask import render_template

from ..config import FALLBACK_CACHE_SECONDS, SPOTIFY_LOGO_B64
from ..spotify_client import SpotifyError, spotify_request
from ..theming import resolve_background, resolve_bar_count, resolve_theme

logger = logging.getLogger(__name__)

_last_successful_svg = None
_last_successful_svg_at = 0
_last_track = None


def _generate_bars(bar_count, color):
    bars = "".join(["<div class='bar'></div>" for _ in range(bar_count)])
    css = "<style>.bar-container { animation-duration: 2s; }"
    for i in range(bar_count):
        css += f""".bar:nth-child({i + 1}) {{
                animation-duration: {randint(500, 750)}ms;
                background: {color};
            }}"""
    css += "</style>"
    return f"{bars}{css}"


def _format_duration(ms):
    total_seconds = max(0, ms) // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def _extract_artist(item):
    artists = item.get("artists", [])
    return artists[0].get("name", "") if artists else ""


def _render(query_params, song="Not listening right now", artist="", progress_ms=None, duration_ms=None):
    theme = resolve_theme(query_params.get("theme"))
    background = resolve_background(query_params.get("bg"))
    bar_count = resolve_bar_count(query_params.get("bars"))

    progress_percent = elapsed = total = None
    if progress_ms is not None and duration_ms:
        progress_percent = min(100, round((progress_ms / duration_ms) * 100, 2))
        elapsed = _format_duration(progress_ms)
        total = _format_duration(duration_ms)

    return render_template(
        "now_playing.html",
        bars=_generate_bars(bar_count, theme["accent"]),
        artist=artist,
        song=song,
        logo=SPOTIFY_LOGO_B64,
        text_color=theme["text"],
        muted_color=theme["muted"],
        accent_color=theme["accent"],
        background=background,
        progress_percent=progress_percent,
        elapsed=elapsed,
        total=total,
    )


def render(query_params):
    """Render the now-playing widget; never leaks an upstream error."""
    global _last_successful_svg, _last_successful_svg_at, _last_track

    try:
        current = spotify_request("me/player/currently-playing")
        is_playing = current.get("is_playing", False) if current else False
        item = current.get("item") if is_playing and current else None

        if item and item.get("name"):
            svg = _render(
                query_params,
                song=item["name"],
                artist=_extract_artist(item),
                progress_ms=current.get("progress_ms"),
                duration_ms=item.get("duration_ms"),
            )
            _last_track = item
            _last_successful_svg = svg
            _last_successful_svg_at = monotonic()
            return svg

        recent = spotify_request("me/player/recently-played?limit=1")
        recent_items = recent.get("items", []) if recent else []
        item = recent_items[0].get("track") if recent_items else None

        if not item or not item.get("name"):
            item = _last_track

        if not item or not item.get("name"):
            return _render(query_params)

        svg = _render(query_params, song=item["name"], artist=_extract_artist(item))
        _last_track = item
        _last_successful_svg = svg
        _last_successful_svg_at = monotonic()
        return svg
    except (SpotifyError, AttributeError, IndexError, KeyError, TypeError):
        logger.warning("Spotify unavailable; serving a safe fallback")
        if _last_track and _last_track.get("name"):
            svg = _render(query_params, song=_last_track["name"], artist=_extract_artist(_last_track))
            _last_successful_svg = svg
            _last_successful_svg_at = monotonic()
            return svg
        if (
            _last_successful_svg
            and monotonic() - _last_successful_svg_at < FALLBACK_CACHE_SECONDS
        ):
            return _last_successful_svg
        return _render(query_params)
