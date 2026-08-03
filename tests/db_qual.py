"""Database qualification tests for the study tracker.

These tests validate CRUD operations, relationships, and constraints for the
AreasOfKnowledge, Resources, StudySessions, ReinforcementPoints, and
ReinforcementSessions tables.

Run with:
    pytest tests/db_qual.py -v
"""
import sqlite3
from datetime import date, timedelta

import pytest

from tests import helpers


# -----------------------------------------------------------------------------
# Areas of Knowledge
# -----------------------------------------------------------------------------

def test_create_area(db):
    area_id = db.create_area("Machine Learning", "ML studies", 100.0)
    area = db.get_area(area_id)
    assert area["name"] == "Machine Learning"
    assert area["description"] == "ML studies"
    assert area["goal_hours"] == 100.0


def test_get_all_areas(db):
    db.create_area("Area A", "", 10.0)
    db.create_area("Area B", "", 20.0)
    areas = db.get_all_areas()
    assert len(areas) == 2
    assert {a["name"] for a in areas} == {"Area A", "Area B"}


def test_update_area(db, area):
    db.update_area(area["id"], "Advanced ML", "Advanced topics", 200.0)
    updated = db.get_area(area["id"])
    assert updated["name"] == "Advanced ML"
    assert updated["description"] == "Advanced topics"
    assert updated["goal_hours"] == 200.0


def test_delete_area(db):
    area_id = db.create_area("Temp Area", "", 10.0)
    db.delete_area(area_id)
    assert db.get_area(area_id) is None


def test_delete_area_with_resources_fails(db, resource):
    with pytest.raises(sqlite3.IntegrityError):
        db.delete_area(resource["area_id"])


# -----------------------------------------------------------------------------
# Resources
# -----------------------------------------------------------------------------

def test_create_resource(db, area):
    resource = helpers.create_resource(
        db,
        area_id=area["id"],
        name="Deep Learning Book",
        resource_type="book",
        status="not started",
        author="Ian Goodfellow",
    )
    assert resource["name"] == "Deep Learning Book"
    assert resource["area_id"] == area["id"]
    assert resource["type"] == "book"
    assert resource["status"] == "not started"
    assert resource["author"] == "Ian Goodfellow"


def test_create_resource_invalid_type(db, area):
    with pytest.raises(sqlite3.IntegrityError):
        db.create_resource("Bad Resource", area["id"], "invalid_type", "not started", "", "")


def test_create_resource_invalid_status(db, area):
    with pytest.raises(sqlite3.IntegrityError):
        db.create_resource("Bad Resource", area["id"], "book", "invalid_status", "", "")


def test_get_all_resources(db, area):
    helpers.create_resource(db, area["id"], "Resource A", "book", "not started")
    helpers.create_resource(db, area["id"], "Resource B", "video", "in progress")
    resources = db.get_all_resources()
    assert len(resources) == 2


def test_get_all_resources_filter_by_area(db, area):
    other_area_id = db.create_area("Other Area", "", 10.0)
    helpers.create_resource(db, area["id"], "In Area", "book", "not started")
    helpers.create_resource(db, other_area_id, "Other Area Resource", "book", "not started")
    resources = db.get_all_resources(area_id=area["id"])
    assert len(resources) == 1
    assert resources[0]["name"] == "In Area"


def test_get_all_resources_filter_by_status(db, area):
    helpers.create_resource(db, area["id"], "In Progress Resource", "book", "in progress")
    helpers.create_resource(db, area["id"], "Not Started Resource", "book", "not started")
    resources = db.get_all_resources(status="in progress")
    assert len(resources) == 1
    assert resources[0]["name"] == "In Progress Resource"


def test_update_resource(db, resource, area):
    db.update_resource(
        resource["id"],
        "Updated Resource",
        area["id"],
        "course",
        "in progress",
        "New Author",
        "Updated notes",
    )
    updated = db.get_resource(resource["id"])
    assert updated["name"] == "Updated Resource"
    assert updated["type"] == "course"
    assert updated["status"] == "in progress"
    assert updated["author"] == "New Author"
    assert updated["notes"] == "Updated notes"


def test_update_resource_changes_area(db, resource):
    new_area_id = db.create_area("New Area", "", 50.0)
    db.update_resource(
        resource["id"],
        resource["name"],
        new_area_id,
        resource["type"],
        resource["status"],
        resource.get("author", ""),
        resource.get("notes", ""),
    )
    updated = db.get_resource(resource["id"])
    assert updated["area_id"] == new_area_id


def test_delete_resource(db):
    area = helpers.create_area(db, "Area")
    resource = helpers.create_resource(db, area["id"])
    db.delete_resource(resource["id"])
    assert db.get_resource(resource["id"]) is None


def test_delete_resource_cascades_sessions(db, resource):
    helpers.create_session(db, resource["id"], hours=2.0)
    db.delete_resource(resource["id"])
    assert db.get_resource(resource["id"]) is None
    assert db.get_sessions_by_resource(resource["id"]) == []


# -----------------------------------------------------------------------------
# Study Sessions
# -----------------------------------------------------------------------------

def test_create_session(db, resource):
    session_id = helpers.create_session(
        db, resource["id"], hours=2.5, session_date=date(2024, 1, 1), note="Chapter 1"
    )
    sessions = db.get_sessions_by_resource(resource["id"])
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_id
    assert sessions[0]["hours"] == 2.5
    assert sessions[0]["note"] == "Chapter 1"


def test_get_sessions_by_resource_order(db, resource):
    helpers.create_session(db, resource["id"], hours=1.0, session_date=date(2024, 1, 1))
    helpers.create_session(db, resource["id"], hours=2.0, session_date=date(2024, 1, 2))
    sessions = db.get_sessions_by_resource(resource["id"])
    assert len(sessions) == 2
    assert sessions[0]["date"] == "2024-01-02"
    assert sessions[1]["date"] == "2024-01-01"


def test_resource_total_hours(db, resource):
    helpers.create_session(db, resource["id"], hours=2.0)
    helpers.create_session(db, resource["id"], hours=3.0)
    assert db.get_resource_total_hours(resource["id"]) == 5.0


def test_resource_session_count(db, resource):
    helpers.create_session(db, resource["id"], hours=1.0)
    helpers.create_session(db, resource["id"], hours=1.0)
    assert db.get_resource_session_count(resource["id"]) == 2


def test_create_session_invalid_resource_fails(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.create_session(9999, date.today(), 1.0, "")


# -----------------------------------------------------------------------------
# Reinforcement Points
# -----------------------------------------------------------------------------

def test_create_reinforcement_point(db, resource):
    point = helpers.create_reinforcement_point(
        db,
        resource["id"],
        description="Review Chapter 1",
        completion_date=date(2024, 1, 15),
    )
    assert point["description"] == "Review Chapter 1"
    assert point["resource_id"] == resource["id"]
    assert point["session_id"] is None


def test_get_reinforcement_points_excludes_completed(db, resource):
    point_id = db.create_reinforcement_point(
        resource["id"], "Point", date.today() + timedelta(days=1)
    )
    db.create_reinforcement_session([point_id], 1.0, "Review")
    incomplete_points = db.get_reinforcement_points(include_completed=False)
    assert not any(p["id"] == point_id for p in incomplete_points)


def test_get_reinforcement_points_includes_completed(db, resource):
    point_id = db.create_reinforcement_point(
        resource["id"], "Point", date.today() + timedelta(days=1)
    )
    db.create_reinforcement_session([point_id], 1.0, "Review")
    all_points = db.get_reinforcement_points(include_completed=True)
    assert any(p["id"] == point_id for p in all_points)


def test_update_reinforcement_point(db, resource):
    point = helpers.create_reinforcement_point(db, resource["id"])
    new_date = date(2024, 12, 31)
    db.update_reinforcement_point(point["id"], "Updated description", new_date)
    updated = db.get_reinforcement_point(point["id"])
    assert updated["description"] == "Updated description"
    assert updated["completion_date"] == "2024-12-31"


def test_delete_reinforcement_point(db, resource):
    point = helpers.create_reinforcement_point(db, resource["id"])
    db.delete_reinforcement_point(point["id"])
    assert db.get_reinforcement_point(point["id"]) is None


def test_delete_completed_reinforcement_point_is_noop(db, resource):
    point_id = db.create_reinforcement_point(resource["id"], "Point", date.today())
    db.create_reinforcement_session([point_id], 1.0, "Review")
    db.delete_reinforcement_point(point_id)
    # Point is completed (has session_id), so delete is a no-op
    assert db.get_reinforcement_point(point_id) is not None


# -----------------------------------------------------------------------------
# Reinforcement Sessions
# -----------------------------------------------------------------------------

def test_create_reinforcement_session(db, resource):
    point_id = db.create_reinforcement_point(
        resource["id"], "Point 1", date.today() + timedelta(days=1)
    )
    session_id = db.create_reinforcement_session([point_id], 1.5, "Review")
    sessions = db.get_reinforcement_sessions()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_id
    assert sessions[0]["hours"] == 1.5
    assert sessions[0]["point_count"] == 1


def test_create_reinforcement_session_creates_study_session(db, resource):
    point_id = db.create_reinforcement_point(
        resource["id"], "Point 1", date.today() + timedelta(days=1)
    )
    db.create_reinforcement_session([point_id], 2.0, "Review")
    sessions = db.get_sessions_by_resource(resource["id"])
    assert len(sessions) == 1
    assert sessions[0]["hours"] == 2.0
    assert sessions[0]["type"] == "reinforcement"


def test_create_reinforcement_session_multiple_points(db, resource):
    point_1 = db.create_reinforcement_point(
        resource["id"], "Point 1", date.today() + timedelta(days=1)
    )
    point_2 = db.create_reinforcement_point(
        resource["id"], "Point 2", date.today() + timedelta(days=2)
    )
    db.create_reinforcement_session([point_1, point_2], 2.0, "Review")
    sessions = db.get_sessions_by_resource(resource["id"])
    # One study session is created per point, each receiving an equal share of hours.
    assert len(sessions) == 2
    assert sum(s["hours"] for s in sessions) == 2.0
    assert all(s["hours"] == 1.0 for s in sessions)


def test_create_reinforcement_session_requires_points(db):
    with pytest.raises(ValueError):
        db.create_reinforcement_session([], 1.0, "Review")


def test_create_reinforcement_session_requires_positive_hours(db, resource):
    point_id = db.create_reinforcement_point(
        resource["id"], "Point", date.today() + timedelta(days=1)
    )
    with pytest.raises(ValueError):
        db.create_reinforcement_session([point_id], 0.0, "Review")


def test_delete_reinforcement_session(db, resource):
    point_id = db.create_reinforcement_point(
        resource["id"], "Point", date.today() + timedelta(days=1)
    )
    session_id = db.create_reinforcement_session([point_id], 1.0, "Review")
    db.delete_reinforcement_session(session_id)
    assert db.get_reinforcement_session_points(session_id) == []
    assert not any(s["id"] == session_id for s in db.get_reinforcement_sessions())
    assert db.get_sessions_by_resource(resource["id"]) == []


# -----------------------------------------------------------------------------
# Full Resource Lifecycle
# -----------------------------------------------------------------------------

def test_full_resource_lifecycle(db):
    """End-to-end validation covering all major operations and constraints."""

    # 1. Create area of knowledge
    area_id = db.create_area("Machine Learning", "ML studies", 100.0)
    area = db.get_area(area_id)
    assert area["name"] == "Machine Learning"

    # 2. Create multiple areas
    area2_id = db.create_area("Mathematics", "Math basics", 50.0)
    assert len(db.get_all_areas()) == 2

    # 3. Create resource linked to area
    resource_id = db.create_resource(
        "Deep Learning Book",
        area_id,
        "book",
        "not started",
        "Ian Goodfellow",
        "",
    )
    resource = db.get_resource(resource_id)
    assert resource["name"] == "Deep Learning Book"
    assert resource["area_id"] == area_id

    # 4. Validate resource constraints
    with pytest.raises(sqlite3.IntegrityError):
        db.create_resource("Bad", area_id, "invalid_type", "not started", "", "")
    with pytest.raises(sqlite3.IntegrityError):
        db.create_resource("Bad", area_id, "book", "invalid_status", "", "")

    # 5. Create study sessions
    db.create_session(resource_id, date(2024, 1, 1), 2.0, "Chapter 1")
    db.create_session(resource_id, date(2024, 1, 2), 3.0, "Chapter 2")
    sessions = db.get_sessions_by_resource(resource_id)
    assert len(sessions) == 2
    assert db.get_resource_total_hours(resource_id) == 5.0
    assert db.get_resource_session_count(resource_id) == 2

    # 6. Create reinforcement point and complete it via a reinforcement session
    point_id = db.create_reinforcement_point(
        resource_id, "Review Chapter 1", date(2024, 1, 10)
    )
    db.create_reinforcement_session([point_id], 1.5, "Reinforcement review")
    reinforcement_sessions = db.get_reinforcement_sessions()
    assert len(reinforcement_sessions) == 1

    # 7. Create a standalone reinforcement point for individual deletion
    standalone_point_id = db.create_reinforcement_point(
        resource_id, "Standalone Point", date(2024, 2, 1)
    )

    # 8. Edit resource
    db.update_resource(
        resource_id,
        "Updated Book",
        area_id,
        "course",
        "in progress",
        "New Author",
        "Updated notes",
    )
    updated = db.get_resource(resource_id)
    assert updated["name"] == "Updated Book"
    assert updated["type"] == "course"
    assert updated["status"] == "in progress"

    # 9. Edit area
    db.update_area(area_id, "Advanced ML", "Advanced topics", 200.0)
    updated_area = db.get_area(area_id)
    assert updated_area["name"] == "Advanced ML"
    assert updated_area["goal_hours"] == 200.0

    # 10. Try to delete area with resources — must fail
    with pytest.raises(sqlite3.IntegrityError):
        db.delete_area(area_id)

    # 11. Delete the completed reinforcement session
    # (this also removes the completed point and the linked study session)
    db.delete_reinforcement_session(reinforcement_sessions[0]["id"])
    assert len(db.get_reinforcement_sessions()) == 0
    assert db.get_reinforcement_point(point_id) is None

    # 12. Delete the standalone reinforcement point
    db.delete_reinforcement_point(standalone_point_id)
    assert db.get_reinforcement_point(standalone_point_id) is None

    # 13. Delete resource — must cascade study sessions
    db.delete_resource(resource_id)
    assert db.get_resource(resource_id) is None
    assert db.get_sessions_by_resource(resource_id) == []

    # 14. Delete area now succeeds
    db.delete_area(area_id)
    assert db.get_area(area_id) is None

    # 15. Second area still exists
    assert db.get_area(area2_id) is not None
