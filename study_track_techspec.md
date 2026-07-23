# Study Tracker — Technical & Functional Spec

## Overview
A personal Streamlit + SQLite app to track study progress across resources (books, courses, videos, articles, etc.), organized by area of knowledge, with time logging and simple dashboards.

## Tech Stack
- **Frontend/App:** Streamlit (multipage app)
- **Database:** SQLite
- **Charts:** Native Streamlit charts (`st.bar_chart`, `st.line_chart`)

---

## Data Model

### AreasOfKnowledge
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | required |
| description | TEXT | optional |
| goal_hours | FLOAT | defaults to 10000 (the "10,000 hours" mastery benchmark popularized by experts like Andrej Karpathy); editable per area |
| created_at | DATETIME | auto |

### Resources
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | required, e.g. "AI Engineering by Chip Huyen" |
| area_id | INTEGER FK → AreasOfKnowledge.id | required |
| type | TEXT | book / course / video / article / other |
| status | TEXT | not started / in progress / completed |
| author | TEXT | optional |
| notes | TEXT | optional |
| created_at | DATETIME | auto |

### StudySessions
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| resource_id | INTEGER FK → Resources.id | required, `ON DELETE CASCADE` at DB level |
| date | DATE | required, defaults to today in UI |
| hours | FLOAT | required |
| note | TEXT | optional |

**Foreign key handling:**
- `Resources.area_id` — **no hard DB cascade**; deletion behavior is handled in application logic (see Delete Flows below), since it branches between cascade and reassign.
- `StudySessions.resource_id` — **hard DB-level `ON DELETE CASCADE`**, since deleting a resource always cascades its sessions with no branching needed.

---

## App Structure

```
study_tracker/
├── app.py                        # entry point / home page
├── db.py                         # SQLite connection + schema init + CRUD functions
├── study_tracker.db              # created on first run (default location)
└── pages/
    ├── 1_Areas_of_Knowledge.py
    ├── 2_Resources.py
    └── 3_Dashboard.py
```

---

## Local Database Path

By default, the app creates and uses `study_tracker.db` in the project root. The database path can be overridden with the `STUDY_TRACKER_DB` environment variable:

```bash
STUDY_TRACKER_DB=/path/to/custom.db streamlit run app.py
```

This is useful for:
- Keeping the production database untouched while running tests or experiments.
- Storing the database in a different location (e.g., a synced folder).
- Running isolated test instances without risking personal study data.

If `STUDY_TRACKER_DB` is not set, the app falls back to the default `study_tracker.db` next to `app.py`.

---

## Screens

### 1. Areas of Knowledge

**Main view:** table of all areas — name, description, resource count, total hours studied, goal hours, and progress % toward goal.

**Actions:**
- **Create** — form (name + optional description) → adds new area.
- **Click an area** → **Area Detail view**:
  - Name/description, editable via "Edit" button (reveals pre-filled form with Save/Cancel).
  - List of all Resources in this area (name, type, status, hours logged) — clicking a resource jumps to Resource Detail.
  - Total hours studied in this area, plus progress toward the area's **goal (default 10,000 hours)** — shown as a progress bar (`st.progress`) and "X / 10,000 hours (Y%)".
  - Goal hours is editable from the "Edit" form (defaults to 10000 but can be changed per area).
  - Button to add a new resource, pre-filled with this area.
- **Delete:**
  - If area has 0 resources → simple confirmation ("Are you sure?") → delete immediately.
  - If area has ≥1 resource → dialog with two choices:
    1. **Delete all resources in this area too** — cascades: deletes area, its resources, and their sessions.
    2. **Reassign resources to another area** — dropdown of existing areas + "Create new area" inline option → resources moved, then original area deleted.

### 2. Resources

**Main view:** table of all resources across all areas. Filterable by area and status; sortable by name/hours/last studied. Each row has an inline **"Log hours"** button that opens a small form (date/hours/note) right there, without navigating away — this is the primary, fast way to log study time.

**Actions:**
- **Create** — form (name, area dropdown, type, status, optional author/notes).
- **Log hours (inline, from the table)** — click the button on a resource's row → small form appears (date defaults to today, hours, optional note) → submit → adds a session and updates that row's total hours immediately.
- **Click a resource's name** → **Resource Detail view**:
  - All fields, editable via "Edit" button (pre-filled form with Save/Cancel).
  - Total hours logged, number of sessions, last studied date.
  - Full session history table (date, hours, note), most recent first.
  - "Log hours" button/form here too (date/hours/note) — same mechanism as the inline one on the main Resources table, for when you're already viewing the resource's full detail.
  - Delete button.
- **Delete:**
  - Confirmation: "This will delete the resource and its N logged sessions — are you sure?" → on confirm, cascades (resource + sessions).

### 3. Dashboard (read-only)

- Quick stats: total hours all-time, hours this week, number of resources with status = in progress.
- Bar chart: hours per area.
- Progress bars: hours vs. 10,000-hour goal per area.
- Bar chart or table: hours per resource.
- Line chart: hours over time (daily/weekly aggregated), overall or filterable by area.
- **Recent activity feed** (last N study sessions logged, across all resources, most recent first) — each row clickable → jumps to that resource's detail. (Moved here from the removed "Log Study Time" page.)

---

## Delete Flow Details

### Delete Area
1. Click "Delete" on an area.
2. If area has resources:
   - Show choice: **cascade delete** (area + resources + sessions) OR **reassign** (pick existing area from dropdown, or create a new one inline, then move resources before deleting the area).
3. If area has no resources: simple Yes/Cancel confirmation.

### Delete Resource
1. Click "Delete" on a resource.
2. Confirmation showing count of sessions to be deleted.
3. On confirm: cascade deletes resource + all its sessions.

---

## UI Conventions
- **Editing:** "Edit" button reveals a form pre-filled with current values; Save/Cancel to commit or discard.
- **Confirmations:** Since Streamlit has no native browser confirm dialogs, deletions use a two-step button flow (click "Delete" → shows "Are you sure? [Yes, delete] [Cancel]").

---

## Explicitly Out of Scope (for now)
- No file/document upload for resources (records only, no attachments).
- No target completion dates (only the 10,000-hour goal per area is tracked, not deadlines).
- No tags / many-to-many topic assignment (area of knowledge is a single required field per resource).
- No multi-user support — single local user/app instance.

---

## GitHub Workflow

This project is designed to be a personal, locally-run Streamlit app that anyone can clone and run on their own machine. The repository contains only the application code, not a shared database or user accounts.

### Repository contents
- The full Streamlit app source code (`app.py`, `db.py`, the `pages/` folder).
- A `requirements.txt` file listing Python dependencies.
- This spec document.
- A `.gitignore` that excludes the SQLite database (`study_tracker.db`) and any Python/IDE artifacts.

The SQLite database file is generated locally on first run, so each user has their own private data.

### Initial setup (project owner)
1. Create a new public repository on GitHub.
2. Add the project files and commit them.
3. Push to the `main` branch.
4. In GitHub, set the repository as the upstream remote for the local project.

### Ongoing development workflow
- Work on features and fixes in short-lived branches.
- Merge changes back to `main` via pull requests.
- Keep commits small and focused on one logical change at a time.
- Never commit the SQLite database file; it is personal data and should stay on the local machine.

### How others can use this project
1. Clone the repository from GitHub.
2. Create a local Python virtual environment.
3. Install dependencies from `requirements.txt`.
4. Run the Streamlit app; the database file is created automatically on first launch.
5. Each user’s study data stays in their own local database file and is not pushed back to the repository.

### Files that should stay out of the repository
- `study_tracker.db` — personal SQLite database, created at runtime.
- Any `.env` or local configuration files.
- IDE and cache folders (e.g. `__pycache__/`, `.venv/`, `.idea/`).

This workflow keeps the project open and reusable while ensuring every user owns their own data locally.
