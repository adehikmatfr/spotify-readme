from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"
LOGO_PATH = APP_DIR / "assets" / "spotify_logo.txt"

TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_URL = "https://api.spotify.com/v1"
REQUEST_TIMEOUT = 10
TOKEN_CACHE_SECONDS = 3_000
FALLBACK_CACHE_SECONDS = 300

with LOGO_PATH.open() as f:
    SPOTIFY_LOGO_B64 = f.read().strip()
