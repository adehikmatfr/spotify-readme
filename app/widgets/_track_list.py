from flask import render_template

from ..config import SPOTIFY_LOGO_B64
from ..theming import resolve_background, resolve_theme

HEADER_HEIGHT = 30
ROW_HEIGHT = 22
VERTICAL_PADDING = 16


def render_track_list(query_params, title, tracks):
    theme = resolve_theme(query_params.get("theme"))
    background = resolve_background(query_params.get("bg"))
    height = HEADER_HEIGHT + VERTICAL_PADDING + max(len(tracks), 1) * ROW_HEIGHT

    return render_template(
        "track_list.html",
        title=title,
        tracks=tracks,
        logo=SPOTIFY_LOGO_B64,
        text_color=theme["text"],
        muted_color=theme["muted"],
        accent_color=theme["accent"],
        background=background,
        height=height,
    )
