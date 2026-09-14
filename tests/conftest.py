from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "control-plane"))

from app.main import create_app  # noqa: E402
from app.store import Store  # noqa: E402


@pytest.fixture
def store() -> Store:
    return Store()


@pytest.fixture
def client(store: Store) -> TestClient:
    return TestClient(create_app(store))
