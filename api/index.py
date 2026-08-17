import sys
from pathlib import Path

# Vercel's Python runtime invokes this file directly, so the repository root
# (where the `app` package lives) is not guaranteed to already be on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
