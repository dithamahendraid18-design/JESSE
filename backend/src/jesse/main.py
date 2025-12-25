from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv

# Load .env dari root project: C:\JESSE.01\.env
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from .app import create_app  # import setelah env diload


def main():
    app = create_app()
    settings = app.config["SETTINGS"]
    app.logger.info(f"Starting JESSE backend on port {settings.port}")
    app.run(host="0.0.0.0", port=settings.port, debug=True)


if __name__ == "__main__":
    main()
