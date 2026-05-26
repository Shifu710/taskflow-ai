import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
os.environ["DATABASE_URL"] = "sqlite:///./taskflow_test.db"

import pytest
from fastapi.testclient import TestClient

from app.db.seed import seed_database
from app.db.session import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def guest_headers(client):
    res = client.post("/api/v1/auth/guest")
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}
