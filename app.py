import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "flask-productivity-api-backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from server.app import app

__all__ = ["app"]
