import os

os.environ["USE_MOCK_DATA"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test_erp_ai.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
