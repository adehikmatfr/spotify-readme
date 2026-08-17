import re

# Query-param-driven values end up inside a raw <style> block, so they are
# validated against a strict allowlist/regex rather than trusted as-is.
_HEX_COLOR_RE = re.compile(r"^[0-9a-fA-F]{3}$|^[0-9a-fA-F]{6}$")

THEMES = {
    "light": {"text": "#24292f", "muted": "#57606a", "accent": "#1DB954"},
    "dark": {"text": "#e6edf3", "muted": "#8b949e", "accent": "#1ED760"},
}
DEFAULT_THEME = "light"

MIN_BARS = 4
MAX_BARS = 20
DEFAULT_BAR_COUNT = 12


def resolve_theme(name):
    return THEMES.get((name or "").lower(), THEMES[DEFAULT_THEME])


def resolve_background(value):
    if not value:
        return None
    candidate = value.lstrip("#")
    return f"#{candidate}" if _HEX_COLOR_RE.match(candidate) else None


def resolve_bar_count(value):
    try:
        count = int(value)
    except (TypeError, ValueError):
        return DEFAULT_BAR_COUNT
    return max(MIN_BARS, min(MAX_BARS, count))
