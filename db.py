import os
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

DB_PATH = Path(
    os.environ.get("STUDY_TRACKER_DB", Path(__file__).parent / "study_tracker.db")
)

RESOURCE_TYPES = ["book", "course", "video", "article", "other"]
RESOURCE_STATUSES = ["not started", "in progress", "completed"]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS AreasOfKnowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                goal_hours REAL NOT NULL DEFAULT 10000,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS Resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                area_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('book', 'course', 'video', 'article', 'other')),
                status TEXT NOT NULL CHECK(status IN ('not started', 'in progress', 'completed')),
                author TEXT,
                notes TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (area_id) REFERENCES AreasOfKnowledge(id)
            );

            CREATE TABLE IF NOT EXISTS StudySessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL,
                date DATE NOT NULL,
                hours REAL NOT NULL,
                note TEXT,
                FOREIGN KEY (resource_id) REFERENCES Resources(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_resources_area ON Resources(area_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_resource ON StudySessions(resource_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_date ON StudySessions(date);
            """
        )


# -----------------------------------------------------------------------------
# Areas of Knowledge
# -----------------------------------------------------------------------------

def create_area(name: str, description: str = "", goal_hours: float = 10000.0):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO AreasOfKnowledge (name, description, goal_hours) VALUES (?, ?, ?)",
            (name, description, goal_hours),
        )
        return cur.lastrowid


def get_area(area_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM AreasOfKnowledge WHERE id = ?", (area_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_areas():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM AreasOfKnowledge ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]


def update_area(area_id: int, name: str, description: str, goal_hours: float):
    with get_connection() as conn:
        conn.execute(
            "UPDATE AreasOfKnowledge SET name = ?, description = ?, goal_hours = ? WHERE id = ?",
            (name, description, goal_hours, area_id),
        )


def delete_area(area_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM AreasOfKnowledge WHERE id = ?", (area_id,))


def count_resources_in_area(area_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM Resources WHERE area_id = ?", (area_id,)
        ).fetchone()
        return row[0]


def get_area_total_hours(area_id: int) -> float:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(s.hours), 0)
            FROM StudySessions s
            JOIN Resources r ON s.resource_id = r.id
            WHERE r.area_id = ?
            """,
            (area_id,),
        ).fetchone()
        return float(row[0])


def reassign_resources_to_area(old_area_id: int, new_area_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE Resources SET area_id = ? WHERE area_id = ?",
            (new_area_id, old_area_id),
        )


# -----------------------------------------------------------------------------
# Resources
# -----------------------------------------------------------------------------

def create_resource(
    name: str,
    area_id: int,
    resource_type: str,
    status: str,
    author: str = "",
    notes: str = "",
):
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO Resources (name, area_id, type, status, author, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, area_id, resource_type, status, author, notes),
        )
        return cur.lastrowid


def get_resource(resource_id: int):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT r.*, a.name as area_name
            FROM Resources r
            JOIN AreasOfKnowledge a ON r.area_id = a.id
            WHERE r.id = ?
            """,
            (resource_id,),
        ).fetchone()
        return dict(row) if row else None


def get_all_resources(area_id: int = None, status: str = None):
    query = """
        SELECT r.*, a.name as area_name,
               (SELECT SUM(hours) FROM StudySessions WHERE resource_id = r.id) as total_hours,
               (SELECT COUNT(*) FROM StudySessions WHERE resource_id = r.id) as session_count,
               (SELECT MAX(date) FROM StudySessions WHERE resource_id = r.id) as last_studied
        FROM Resources r
        JOIN AreasOfKnowledge a ON r.area_id = a.id
    """
    params = []
    conditions = []
    if area_id is not None:
        conditions.append("r.area_id = ?")
        params.append(area_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY r.name"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_resources_by_area(area_id: int):
    return get_all_resources(area_id=area_id)


def update_resource(
    resource_id: int,
    name: str,
    area_id: int,
    resource_type: str,
    status: str,
    author: str,
    notes: str,
):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE Resources
            SET name = ?, area_id = ?, type = ?, status = ?, author = ?, notes = ?
            WHERE id = ?
            """,
            (name, area_id, resource_type, status, author, notes, resource_id),
        )


def delete_resource(resource_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM Resources WHERE id = ?", (resource_id,))


def get_resource_total_hours(resource_id: int) -> float:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(hours), 0) FROM StudySessions WHERE resource_id = ?",
            (resource_id,),
        ).fetchone()
        return float(row[0])


def get_resource_session_count(resource_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM StudySessions WHERE resource_id = ?", (resource_id,)
        ).fetchone()
        return row[0]


def get_resource_last_studied(resource_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MAX(date) FROM StudySessions WHERE resource_id = ?", (resource_id,)
        ).fetchone()
        return row[0]


# -----------------------------------------------------------------------------
# Study Sessions
# -----------------------------------------------------------------------------

def create_session(resource_id: int, session_date: date, hours: float, note: str = ""):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO StudySessions (resource_id, date, hours, note) VALUES (?, ?, ?, ?)",
            (resource_id, session_date, hours, note),
        )
        return cur.lastrowid


def get_sessions_by_resource(resource_id: int):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.*, r.name as resource_name, r.area_id
            FROM StudySessions s
            JOIN Resources r ON s.resource_id = r.id
            WHERE s.resource_id = ?
            ORDER BY s.date DESC, s.id DESC
            """,
            (resource_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_recent_sessions(limit: int = 20):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.*, r.name as resource_name, r.area_id
            FROM StudySessions s
            JOIN Resources r ON s.resource_id = r.id
            ORDER BY s.date DESC, s.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_recent_sessions_last_weeks(weeks: int = 2):
    today = date.today()
    cutoff = today - timedelta(weeks=weeks)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.*, r.name as resource_name, r.area_id
            FROM StudySessions s
            JOIN Resources r ON s.resource_id = r.id
            WHERE s.date >= ?
            ORDER BY s.date DESC, s.id DESC
            """,
            (cutoff,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_total_hours_all_time() -> float:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(hours), 0) FROM StudySessions"
        ).fetchone()
        return float(row[0])


def get_hours_this_week() -> float:
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(hours), 0) FROM StudySessions WHERE date >= ?",
            (start_of_week,),
        ).fetchone()
        return float(row[0])


def get_resources_in_progress_count() -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM Resources WHERE status = 'in progress'"
        ).fetchone()
        return row[0]


# -----------------------------------------------------------------------------
# Dashboard aggregations
# -----------------------------------------------------------------------------

def get_hours_per_area():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.name, a.goal_hours,
                   COALESCE(SUM(s.hours), 0) as total_hours
            FROM AreasOfKnowledge a
            LEFT JOIN Resources r ON a.id = r.area_id
            LEFT JOIN StudySessions s ON r.id = s.resource_id
            GROUP BY a.id, a.name
            ORDER BY total_hours DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def get_hours_per_resource():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT r.id, r.name, a.name as area_name,
                   COALESCE(SUM(s.hours), 0) as total_hours
            FROM Resources r
            JOIN AreasOfKnowledge a ON r.area_id = a.id
            LEFT JOIN StudySessions s ON r.id = s.resource_id
            GROUP BY r.id, r.name
            ORDER BY total_hours DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def get_hours_over_time(period: str = "daily", area_id: int = None):
    if period == "daily":
        select = "s.date"
        group_by = "s.date"
    else:
        select = "strftime('%Y-%W', s.date)"
        group_by = "strftime('%Y-%W', s.date)"

    query = f"""
        SELECT {select} as period, COALESCE(SUM(s.hours), 0) as total_hours
        FROM StudySessions s
        JOIN Resources r ON s.resource_id = r.id
    """
    params = []
    conditions = []
    if area_id is not None:
        conditions.append("r.area_id = ?")
        params.append(area_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += f" GROUP BY {group_by} ORDER BY period"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    print("Database initialized at", DB_PATH)
