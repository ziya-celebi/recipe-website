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

# Custom handler to strip /api prefix
class CustomMangum:
    def __init__(self, app):
        self.app = app
        self.mangum_app = Mangum(app)
    
    def __call__(self, event, context):
        # Strip /api prefix from the path
        if 'path' in event:
            original_path = event['path']
            if original_path.startswith('/api'):
                event['path'] = original_path[4:]  # Remove '/api'
                if event['path'] == '':
                    event['path'] = '/'
                # Also update rawPath if it exists
                if 'rawPath' in event:
                    event['rawPath'] = event['path']
        
        return self.mangum_app(event, context)

handler = CustomMangum(app)
