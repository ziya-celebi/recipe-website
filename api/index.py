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
    # Handle /api, /api/, and /api/anything
    if path.startswith("/api"):
        # Remove /api prefix
        remaining = path[4:]
        # If remaining is empty or just /, return /
        if not remaining or remaining == "/":
            return "/"
        return remaining
    return path


def _get_path_from_event(event: dict) -> str:
    """
    Get the actual path from the event, handling Vercel's path parameter passing.
    Vercel may pass the path as a query parameter when using rewrites.
    """
    # Check if path is passed as query parameter (Vercel rewrite behavior)
    query_params = event.get("queryStringParameters") or {}
    if "path" in query_params:
        return "/" + query_params["path"]
    
    # Otherwise use the actual path from the event
    path = event.get("path") or event.get("rawPath") or "/"
    return path


# Custom handler to strip /api prefix
class CustomMangum:
    def __init__(self, app):
        self.app = app
        self.mangum_app = Mangum(app)

    def __call__(self, event, context):
        if isinstance(event, dict):
            # Get the actual path from the event (handles query parameter case)
            actual_path = _get_path_from_event(event)
            stripped_path = _strip_api_prefix(actual_path)
            
            # Debug logging
            print(f"DEBUG: Original event path: {event.get('path')}")
            print(f"DEBUG: Query params: {event.get('queryStringParameters')}")
            print(f"DEBUG: Actual path: {actual_path}")
            print(f"DEBUG: Stripped path: {stripped_path}")
            
            # Update all path fields with the stripped path
            for key in ("path", "rawPath"):
                if key in event:
                    event[key] = stripped_path

            # Handle request context paths
            request_context = event.get("requestContext")
            if isinstance(request_context, dict):
                for key in ("path",):
                    if key in request_context:
                        request_context[key] = stripped_path
                
                http_data = request_context.get("http")
                if isinstance(http_data, dict):
                    for key in ("path",):
                        if key in http_data:
                            http_data[key] = stripped_path

        return self.mangum_app(event, context)


handler = CustomMangum(app)