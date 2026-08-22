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

class PathFixingMangum:
    def __init__(self, app):
        self.app = app
        self.mangum_app = Mangum(app)

    def __call__(self, event, context):
        if isinstance(event, dict):
            # Vercel's serverless function receives the path after /api
            # So /api/recipes comes in as /recipes
            # But sometimes it comes in as / with path as query param
            path = event.get("path", "/")
            
            # Handle the query parameter case
            query_params = event.get("queryStringParameters") or {}
            if "path" in query_params:
                path = "/" + query_params["path"]
            
            # Ensure path starts with /
            if not path.startswith("/"):
                path = "/" + path
            
            # Update the event with the correct path
            event["path"] = path
            if "rawPath" in event:
                event["rawPath"] = path
            
            # Update request context if present
            request_context = event.get("requestContext")
            if isinstance(request_context, dict):
                request_context["path"] = path
                http_data = request_context.get("http")
                if isinstance(http_data, dict):
                    http_data["path"] = path

        return self.mangum_app(event, context)

handler = PathFixingMangum(app)