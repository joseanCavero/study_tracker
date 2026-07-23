# Study Tracker

A personal Streamlit + SQLite app to track study progress across resources (books, courses, videos, articles, etc.), organized by areas of knowledge, with time logging and simple dashboards.

---

## Overview

Study Tracker helps you stay on top of what you are learning. You define **areas of knowledge** (e.g., Machine Learning, Web Development, Design), add **resources** you are studying in each area, and log **study sessions** to record the time you spend. The app then shows you totals, progress toward your goals, and charts of your study activity.

This is a single-user, local application. Your data lives in a local SQLite database file and is not shared or uploaded anywhere.

---

## Tech Stack

- **Frontend / App:** [Streamlit](https://streamlit.io/) (multipage app)
- **Database:** SQLite
- **Charts:** Native Streamlit charts (`st.bar_chart`, `st.line_chart`)
- **Language:** Python 3.9+

---

## Architecture

The app follows a simple three-layer architecture:

```
study_tracker/
├── app.py                        # Entry point / home page
├── db.py                         # Database connection, schema, and CRUD
├── pages/                        # Streamlit multipage views
│   ├── 1_Areas_of_Knowledge.py   # Manage learning areas
│   ├── 2_Resources.py            # Manage resources and log hours
│   └── 3_Dashboard.py            # Stats, charts, and recent activity
├── requirements.txt              # Python dependencies
└── study_tracker.db              # Local SQLite database (created on first run)
```

### Data Model

| Table | Purpose |
|---|---|
| **AreasOfKnowledge** | Topics you study (e.g., "Machine Learning"). Each area has a default 10,000-hour mastery goal that you can edit. |
| **Resources** | Books, courses, videos, articles, or anything else you study. Each resource belongs to one area. |
| **StudySessions** | A single study session linked to a resource, with a date and number of hours. |

Relationships:

- A resource belongs to exactly one area.
- A study session belongs to exactly one resource.
- Deleting a resource automatically deletes its study sessions.
- Deleting an area gives you the choice to either delete its resources too or reassign them to another area.

---

## Features

### 1. Areas of Knowledge

- Create, edit, and delete areas of knowledge.
- Each area has a customizable goal (default is 10,000 hours).
- View a progress bar showing how many hours you have logged toward the goal.
- See a list of all resources inside an area.
- Add a new resource directly from an area’s detail page.

### 2. Resources

- Create resources with name, type, status, author, and notes.
- Types: book, course, video, article, or other.
- Statuses: not started, in progress, completed.
- Filter resources by area or status.
- Sort resources by name, hours logged, or last studied date.
- Log study hours inline from the resources list, or from a resource’s detail page.
- View full session history for each resource.
- Edit or delete any resource.

### 3. Dashboard

- Quick stats: total hours all-time, hours this week, and resources currently in progress.
- Bar chart: hours per area.
- Progress bars: hours vs. goal per area.
- Bar chart: hours per resource.
- Line chart: hours over time, aggregated daily or weekly, and filterable by area.
- Recent activity feed of the latest study sessions with links to the corresponding resource.

---

## Installation

### Prerequisites

- Python 3.9 or newer
- A terminal

### Steps

1. Clone or download the project into a folder.

2. Open a terminal in that folder.

3. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment:

   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

5. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Run the app:

   ```bash
   streamlit run app.py
   ```

7. Open the URL shown in the terminal (usually `http://localhost:8501`) in your browser.

On first run, the app creates a `study_tracker.db` SQLite file next to the app files. This file contains your personal data and is not tracked by Git.

---

## How to Use the App

### Getting Started

1. Go to the **Areas of Knowledge** page.
2. Create your first area (for example, "Machine Learning" or "Web Development").
3. Open that area and click **Add resource** to create a book, course, video, or article.
4. Go to the **Resources** page, find your resource, and click **Log hours** to record a study session.
5. Visit the **Dashboard** to see your progress and recent activity.

### Tracking Study Time

- The fastest way to log time is from the **Resources** page: click the **Log hours** button on any resource row, enter the date and hours, and submit.
- You can also log hours from a resource’s detail page.

### Managing Areas

- Click any area in the list to open its detail page.
- From the detail page you can edit the name, description, and goal hours.
- You can delete an area. If it has resources, you choose whether to delete the resources too or move them to another area.

### Managing Resources

- Click any resource name in the **Resources** page to open its detail page.
- From the detail page you can edit all fields, view the full session history, log more hours, or delete the resource.
- Deleting a resource also deletes all its logged sessions.

---

## Notes for Users

- **Data is local.** Your study data is stored in `study_tracker.db` on your computer. It is not sent to any server.
- **One database per installation.** If you clone the project on a different machine, it will start with a fresh, empty database.
- **Do not commit the database.** The `study_tracker.db` file is ignored by Git so you do not accidentally publish your personal study data.

---

## Project Status

This is a personal study tool. The current scope is intentionally simple:

- No file attachments for resources.
- No target completion dates.
- No tags or many-to-many topics.
- No multi-user support.

Future enhancements could include cloud sync, target dates, or resource attachments.
