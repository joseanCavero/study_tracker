import importlib
import os
import tempfile
from datetime import date
from pathlib import Path

import pytest


@pytest.fixture
def db():
    """Yield a fresh, initialized db module backed by a temp database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_study_tracker.db"
        os.environ["STUDY_TRACKER_DB"] = str(db_path)
        import db as db_module
        importlib.reload(db_module)
        db_module.init_db()
        yield db_module


@pytest.fixture
def area(db):
    """Create and return a sample area of knowledge."""
    area_id = db.create_area("Machine Learning", "ML studies", 100.0)
    return db.get_area(area_id)


@pytest.fixture
def resource(db, area):
    """Create and return a sample resource linked to the area fixture."""
    resource_id = db.create_resource(
        name="Deep Learning Book",
        area_id=area["id"],
        resource_type="book",
        status="not started",
        author="Ian Goodfellow",
        notes="",
    )
    return db.get_resource(resource_id)


@pytest.fixture
def session(db, resource):
    """Create and return a sample study session for the resource fixture."""
    session_id = db.create_session(
        resource_id=resource["id"],
        session_date=date(2024, 1, 1),
        hours=2.0,
        note="Chapter 1",
    )
    return {"id": session_id, "resource_id": resource["id"]}


@pytest.fixture
def reinforcement_point(db, resource):
    """Create and return a sample reinforcement point for the resource fixture."""
    point_id = db.create_reinforcement_point(
        resource_id=resource["id"],
        description="Review Chapter 1",
        completion_date=date(2024, 1, 10),
    )
    return db.get_reinforcement_point(point_id)
