"""Seed script - creates all tables. Runtime data loaded from O*NET CSVs via onet_loader."""
import sys
import os

# In Docker, repo root is /app and backend is /app/backend
_backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if not os.path.isdir(_backend_dir):
    _backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _backend_dir)

from app.models.database import engine
from app.models.models import Base


if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
