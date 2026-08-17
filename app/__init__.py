from flask import Flask, Response, request

from .config import TEMPLATES_DIR
from .widgets import now_playing, recently_played, top_tracks

CACHE_CONTROL = "public, s-maxage=60, stale-while-revalidate=300"


def create_app():
    app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

    def _svg_response(svg):
        resp = Response(svg, mimetype="image/svg+xml")
        resp.headers["Cache-Control"] = CACHE_CONTROL
        return resp

    @app.route("/api/top")
    def top_tracks_widget():
        return _svg_response(top_tracks.render(request.args))

    @app.route("/api/recent")
    def recently_played_widget():
        return _svg_response(recently_played.render(request.args))

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def now_playing_widget(path):
        return _svg_response(now_playing.render(request.args))

    return app
