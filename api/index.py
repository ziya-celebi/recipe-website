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

# Configure Mangum to strip the /api prefix
handler = Mangum(app, api_gateway_base_path="/api")
