"""Reusable helper functions for db qualification tests."""
from datetime import date


def create_area(db, name="Area", description="", goal_hours=100.0):
    """Create an area of knowledge and return its full record."""
    area_id = db.create_area(name, description, goal_hours)
    return db.get_area(area_id)


def create_resource(
    db,
    area_id,
    name="Resource",
    resource_type="book",
    status="not started",
    author="",
    notes="",
):
    """Create a resource linked to an area and return its full record."""
    resource_id = db.create_resource(name, area_id, resource_type, status, author, notes)
    return db.get_resource(resource_id)


def create_session(
    db, resource_id, hours=1.0, session_date=None, note=""
):
    """Create a study session and return its ID."""
    session_date = session_date or date.today()
    return db.create_session(resource_id, session_date, hours, note)


def create_reinforcement_point(
    db, resource_id, description="Point", completion_date=None
):
    """Create a reinforcement point and return its full record."""
    completion_date = completion_date or date.today()
    point_id = db.create_reinforcement_point(resource_id, description, completion_date)
    return db.get_reinforcement_point(point_id)


def create_reinforcement_session(db, point_ids, hours=1.0, note=""):
    """Create a reinforcement session and return the session record."""
    db.create_reinforcement_session(point_ids, hours, note)
    sessions = db.get_reinforcement_sessions()
    return sessions[0]
