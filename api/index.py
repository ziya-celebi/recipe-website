from pathlib import Path
import sys
import os

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set data directory for serverless environment
os.environ["RECIPE_DATA_DIR"] = "/tmp/recipe_data"

# Add backend src directory to Python path
backend_src = backend_dir / "src"
if backend_src.exists():
    sys.path.insert(0, str(backend_src))

from mangum import Mangum
from main import app


def _strip_api_prefix(path: str | None) -> str | None:
    if not path:
        return path
    if path == "/api":
        return "/"
    if path.startswith("/api/"):
        return path[4:] or "/"
    if path.startswith("/api") and len(path) > 4:
        return path[4:] or "/"
    return path


# Custom handler to strip /api prefix
class CustomMangum:
    def __init__(self, app):
        self.app = app
        self.mangum_app = Mangum(app)

    def __call__(self, event, context):
        if isinstance(event, dict):
            for key in ("path", "rawPath"):
                if key in event:
                    event[key] = _strip_api_prefix(event[key])

            request_context = event.get("requestContext")
            if isinstance(request_context, dict):
                request_context["path"] = _strip_api_prefix(request_context.get("path"))
                http_data = request_context.get("http")
                if isinstance(http_data, dict):
                    http_data["path"] = _strip_api_prefix(http_data.get("path"))

            if "path" in event and event["path"] == "/":
                if "rawPath" in event and event["rawPath"] == "/":
                    event["rawPath"] = "/"

        return self.mangum_app(event, context)


handler = CustomMangum(app)