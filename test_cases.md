# Database Qualification Test Cases

This document catalogs the test cases implemented in `tests/db_qual.py` for the study tracker database layer.

## Test Infrastructure

- **Framework:** pytest
- **Test file:** `tests/db_qual.py`
- **Fixtures:** `tests/conftest.py`
- **Helpers:** `tests/helpers.py`
- **Database isolation:** Each test receives a fresh, temporary SQLite database via a
  `tempfile.TemporaryDirectory` and the `STUDY_TRACKER_DB` environment variable.
- **Run command:**
  ```bash
  pytest tests/db_qual.py -v
  ```

## Test Fixtures

| Fixture | Description |
|---------|-------------|
| `db` | A freshly initialized `db` module backed by a temporary database file. |
| `area` | A sample `AreasOfKnowledge` row named "Machine Learning". |
| `resource` | A sample `Resources` row linked to the `area` fixture. |
| `session` | A sample `StudySessions` row linked to the `resource` fixture. |
| `reinforcement_point` | A sample `ReinforcementPoints` row linked to the `resource` fixture. |

## Areas of Knowledge Tests

| Test Case ID | Function | Description | Preconditions | Steps | Expected Result |
|--------------|----------|-------------|---------------|-------|-----------------|
| TC-AREA-001 | `test_create_area` | Create an area of knowledge. | None | Call `create_area(name, description, goal_hours)`. | `get_area(id)` returns the created area with matching fields. |
| TC-AREA-002 | `test_get_all_areas` | Retrieve all areas. | None | Create two areas and call `get_all_areas()`. | Returns both areas. |
| TC-AREA-003 | `test_update_area` | Update an existing area. | Area exists. | Call `update_area(...)` with new name/description/goal. | `get_area(id)` reflects the updated values. |
| TC-AREA-004 | `test_delete_area` | Delete an empty area. | Area exists with no resources. | Call `delete_area(id)`. | `get_area(id)` returns `None`. |
| TC-AREA-005 | `test_delete_area_with_resources_fails` | Deleting an area with resources is rejected. | Area exists with a linked resource. | Call `delete_area(area_id)`. | Raises `sqlite3.IntegrityError`. |

## Resources Tests

| Test Case ID | Function | Description | Preconditions | Steps | Expected Result |
|--------------|----------|-------------|---------------|-------|-----------------|
| TC-RES-001 | `test_create_resource` | Create a resource linked to an area. | Area exists. | Call `create_resource(...)` with valid data. | `get_resource(id)` returns the resource with correct area, type, status, author. |
| TC-RES-002 | `test_create_resource_invalid_type` | Invalid resource type is rejected. | Area exists. | Call `create_resource(...)` with `resource_type="invalid_type"`. | Raises `sqlite3.IntegrityError`. |
| TC-RES-003 | `test_create_resource_invalid_status` | Invalid resource status is rejected. | Area exists. | Call `create_resource(...)` with `status="invalid_status"`. | Raises `sqlite3.IntegrityError`. |
| TC-RES-004 | `test_get_all_resources` | Retrieve all resources. | Area exists with two resources. | Call `get_all_resources()`. | Returns both resources. |
| TC-RES-005 | `test_get_all_resources_filter_by_area` | Filter resources by area. | Two areas, each with one resource. | Call `get_all_resources(area_id=...)`. | Returns only the resource from the requested area. |
| TC-RES-006 | `test_get_all_resources_filter_by_status` | Filter resources by status. | Area with two resources of different statuses. | Call `get_all_resources(status=...)`. | Returns only resources matching the status. |
| TC-RES-007 | `test_update_resource` | Update a resource. | Resource exists. | Call `update_resource(...)` with new values. | `get_resource(id)` reflects the updated values. |
| TC-RES-008 | `test_update_resource_changes_area` | Move a resource to a different area. | Resource and a new area exist. | Call `update_resource(...)` with `area_id=new_area_id`. | `get_resource(id)` shows the new area. |
| TC-RES-009 | `test_delete_resource` | Delete a resource. | Resource exists with no sessions. | Call `delete_resource(id)`. | `get_resource(id)` returns `None`. |
| TC-RES-010 | `test_delete_resource_cascades_sessions` | Deleting a resource cascades its study sessions. | Resource exists with one session. | Call `delete_resource(id)`. | Resource and its sessions are removed. |

## Study Sessions Tests

| Test Case ID | Function | Description | Preconditions | Steps | Expected Result |
|--------------|----------|-------------|---------------|-------|-----------------|
| TC-SES-001 | `test_create_session` | Create a study session for a resource. | Resource exists. | Call `create_session(...)`. | `get_sessions_by_resource(id)` returns the session. |
| TC-SES-002 | `test_get_sessions_by_resource_order` | Sessions are returned newest first. | Resource with two sessions on different dates. | Call `get_sessions_by_resource(id)`. | Sessions are ordered by date descending. |
| TC-SES-003 | `test_resource_total_hours` | Total hours for a resource is summed correctly. | Resource with two sessions. | Call `get_resource_total_hours(id)`. | Returns the sum of session hours. |
| TC-SES-004 | `test_resource_session_count` | Session count for a resource is correct. | Resource with two sessions. | Call `get_resource_session_count(id)`. | Returns `2`. |
| TC-SES-005 | `test_create_session_invalid_resource_fails` | Session for a non-existent resource is rejected. | None | Call `create_session(9999, ...)`. | Raises `sqlite3.IntegrityError`. |

## Reinforcement Points Tests

| Test Case ID | Function | Description | Preconditions | Steps | Expected Result |
|--------------|----------|-------------|---------------|-------|-----------------|
| TC-RP-001 | `test_create_reinforcement_point` | Create a reinforcement point. | Resource exists. | Call `create_reinforcement_point(...)`. | `get_reinforcement_point(id)` returns the point with `session_id=None`. |
| TC-RP-002 | `test_get_reinforcement_points_excludes_completed` | Completed points are excluded by default. | One point completed via a reinforcement session. | Call `get_reinforcement_points(include_completed=False)`. | Completed point is not included. |
| TC-RP-003 | `test_get_reinforcement_points_includes_completed` | Completed points can be included. | One point completed via a reinforcement session. | Call `get_reinforcement_points(include_completed=True)`. | Completed point is included. |
| TC-RP-004 | `test_update_reinforcement_point` | Update an incomplete point. | Incomplete point exists. | Call `update_reinforcement_point(...)`. | Point reflects updated description and completion date. |
| TC-RP-005 | `test_delete_reinforcement_point` | Delete an incomplete point. | Incomplete point exists. | Call `delete_reinforcement_point(id)`. | `get_reinforcement_point(id)` returns `None`. |
| TC-RP-006 | `test_delete_completed_reinforcement_point_is_noop` | Completed points cannot be deleted individually. | Point is completed via a reinforcement session. | Call `delete_reinforcement_point(id)`. | Point remains because `session_id` is not `NULL`. |

## Reinforcement Sessions Tests

| Test Case ID | Function | Description | Preconditions | Steps | Expected Result |
|--------------|----------|-------------|---------------|-------|-----------------|
| TC-RS-001 | `test_create_reinforcement_session` | Create a reinforcement session. | One incomplete point exists. | Call `create_reinforcement_session([point_id], hours, note)`. | `get_reinforcement_sessions()` returns the session with `point_count=1`. |
| TC-RS-002 | `test_create_reinforcement_session_creates_study_session` | A reinforcement session creates a study session. | One incomplete point exists. | Call `create_reinforcement_session([point_id], 2.0, ...)`. | `get_sessions_by_resource(...)` includes a `reinforcement` session with the same hours. |
| TC-RS-003 | `test_create_reinforcement_session_multiple_points` | Hours are split across multiple points. | Two incomplete points for the same resource. | Call `create_reinforcement_session([p1, p2], 2.0, ...)`. | Two study sessions are created, each with `hours = 1.0` (2.0 / 2). |
| TC-RS-004 | `test_create_reinforcement_session_requires_points` | Empty point list is rejected. | None | Call `create_reinforcement_session([], ...)`. | Raises `ValueError`. |
| TC-RS-005 | `test_create_reinforcement_session_requires_positive_hours` | Non-positive hours are rejected. | One incomplete point exists. | Call `create_reinforcement_session([point_id], 0.0, ...)`. | Raises `ValueError`. |
| TC-RS-006 | `test_delete_reinforcement_session` | Delete a reinforcement session. | One completed point and session exist. | Call `delete_reinforcement_session(id)`. | Session, its point, and its study session are removed. |

## Full Resource Lifecycle Test

| Test Case ID | Function | Description | Steps | Expected Result |
|--------------|----------|-------------|-------|-----------------|
| TC-LIFE-001 | `test_full_resource_lifecycle` | End-to-end validation of the entire data model. | 1. Create area.<br>2. Create second area.<br>3. Create resource linked to first area.<br>4. Attempt invalid resource type and status.<br>5. Create two study sessions.<br>6. Create a reinforcement point and complete it via a reinforcement session.<br>7. Create a standalone reinforcement point.<br>8. Update resource.<br>9. Update area.<br>10. Attempt to delete area with resources (must fail).<br>11. Delete reinforcement session.<br>12. Delete standalone reinforcement point.<br>13. Delete resource.<br>14. Delete area.<br>15. Verify second area still exists. | All intermediate assertions pass, and the database ends in a clean state with only the second area remaining. |

## Notes

- Foreign key constraints are enabled via `PRAGMA foreign_keys = ON`.
- Resource `type` must be one of: `book`, `course`, `video`, `article`, `claude project`, `other`.
- Resource `status` must be one of: `not started`, `in progress`, `completed`.
- `delete_reinforcement_session` cascades: it removes the session, its linked points, and the reinforcement study sessions.
- `delete_resource` cascades its linked study sessions via the `ON DELETE CASCADE` foreign key.
- `delete_area` does **not** cascade resources; it raises a foreign-key violation if resources are still linked.
