import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "skill-api"))

from src.main import app  # noqa: F401 — exposed for uvicorn
