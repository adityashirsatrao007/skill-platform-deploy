"""
pytest conftest.py for Skill Intelligence Platform backend.
Mocks heavy ML dependencies, sets up SQLite in-memory test DB.
"""

import sys
import types
from unittest.mock import MagicMock

# Pre-import mocks — MUST happen before any app import
_mock_st = types.ModuleType("sentence_transformers")
_mock_st.SentenceTransformer = MagicMock(return_value=MagicMock(encode=MagicMock(return_value=MagicMock())))
sys.modules["sentence_transformers"] = _mock_st

_mock_np = types.ModuleType("numpy")
_mock_np.array = MagicMock()
_mock_np.dot = MagicMock(return_value=MagicMock())
_mock_np.linalg = MagicMock()
_mock_np.argsort = MagicMock(return_value=MagicMock())
sys.modules["numpy"] = _mock_np

_mock_torch = types.ModuleType("torch")
sys.modules["torch"] = _mock_torch

_mock_transformers = types.ModuleType("transformers")
_mock_transformers.pipeline = MagicMock()
sys.modules["transformers"] = _mock_transformers

_mock_spacy = types.ModuleType("spacy")
_mock_spacy.load = MagicMock()
sys.modules["spacy"] = _mock_spacy

_mock_redis = types.ModuleType("redis")
_mock_redis.from_url = MagicMock(return_value=MagicMock(ping=MagicMock(), get=MagicMock(return_value=None), setex=MagicMock(), delete=MagicMock()))
sys.modules["redis"] = _mock_redis

_mock_pypdf2 = types.ModuleType("PyPDF2")
_mock_pypdf2.PdfReader = MagicMock()
sys.modules["PyPDF2"] = _mock_pypdf2

_mock_docx = types.ModuleType("docx")
_mock_docx.Document = MagicMock()
sys.modules["docx"] = _mock_docx

_mock_pptx = types.ModuleType("pptx")
_mock_pptx.Presentation = MagicMock()
sys.modules["pptx"] = _mock_pptx

for mod in ["nltk", "sklearn", "qdrant_client", "celery", "google.cloud", "google.cloud.storage"]:
    sys.modules[mod] = types.ModuleType(mod)

# Now safe to import app
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.models.database import Base, get_db
from app.models import models as _models

TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def override_get_db():
    def _override():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    from app.main import app
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def client():
    from app.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def auth_token(client):
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "Test123!",
        "full_name": "Test User",
        "designation": "Analyst",
        "department": "Statistics",
    })
    resp = client.post("/api/auth/login", data={"username": "test@example.com", "password": "Test123!"})
    return f"Bearer {resp.json()['access_token']}"


@pytest.fixture()
def auth_headers(auth_token):
    return {"Authorization": auth_token}
