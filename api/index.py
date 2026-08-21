from pathlib import Path
import sys

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from mangum import Mangum
from main import app

handler = Mangum(app)
