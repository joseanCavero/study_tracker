import streamlit as st
from datetime import date, timedelta
from db import (
    init_db,
    get_all_resources,
    get_reinforcement_points,
    get_reinforcement_point,
    create_reinforcement_point,
    update_reinforcement_point,
    delete_reinforcement_point,
    create_reinforcement_session,
    get_reinforcement_sessions,
    delete_reinforcement_session,
)

st.set_page_config(page_title="Reinforcement Learning", page_icon="🔄")

init_db()

st.title("🔄 Reinforcement Learning")

if "editing_point_id" not in st.session_state:
    st.session_state.editing_point_id = None
if "delete_session_id" not in st.session_state:
    st.session_state.delete_session_id = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def status_badge(status: str) -> str:
    return {
        "On track": "🟡 On track",
        "Overdue": "🔴 Overdue",
        "Complete": "🟢 Complete",
    }.get(status, status)


def clear_edit():
    st.session_state.editing_point_id = None
    st.session_state.delete_session_id = None


# -----------------------------------------------------------------------------
# Create reinforcement point
# -----------------------------------------------------------------------------
with st.expander("➕ Create reinforcement point", expanded=False):
    resources = get_all_resources()
    if not resources:
        st.warning("Create a resource first.")
    else:
        resource_options = {
            f"{r['name']} ({r['area_name']})": r["id"] for r in resources
        }
        with st.form("create_reinforcement_point_form"):
            selected_resource_label = st.selectbox(
                "Resource", options=list(resource_options.keys())
            )
            description = st.text_area("What needs to be reviewed")
            completion_date = st.date_input(
                "Completion date",
                value=date.today() + timedelta(days=7),
            )
            submitted = st.form_submit_button("Create point")
            if submitted:
                if not description.strip():
                    st.error("Description is required")
                else:
                    resource_id = resource_options[selected_resource_label]
                    create_reinforcement_point(
                        resource_id, description.strip(), completion_date
                    )
                    st.success("Reinforcement point created")
                    st.rerun()


# -----------------------------------------------------------------------------
# Active points list
# -----------------------------------------------------------------------------
st.subheader("Active reinforcement points")

all_points = get_reinforcement_points(include_completed=False)
active_points = [p for p in all_points if p["status"] in ("On track", "Overdue")]

if not active_points:
    st.info("No active reinforcement points. Create one above.")
else:
    st.markdown(f"Showing **{len(active_points)}** active point(s)")
    for point in active_points:
        with st.container(border=True):
            col_status, col_main, col_actions = st.columns([1, 4, 1])
            with col_status:
                st.markdown(f"**{status_badge(point['status'])}**")
            with col_main:
                st.markdown(f"**{point['resource_name']}**")
                st.markdown(point["description"])
                st.caption(
                    f"Complete by: {point['completion_date']} · Created: {point['created_at'][:10]}"
                )
            with col_actions:
                if st.button("Edit", key=f"edit_point_{point['id']}"):
                    st.session_state.editing_point_id = point["id"]
                    st.session_state.delete_session_id = None
                    st.rerun()


# -----------------------------------------------------------------------------
# Edit active point
# -----------------------------------------------------------------------------
if st.session_state.editing_point_id:
    point = get_reinforcement_point(st.session_state.editing_point_id)
    if not point:
        st.error("Point not found or already completed.")
        clear_edit()
        st.rerun()
    else:
        st.subheader("Edit reinforcement point")
        with st.form("edit_reinforcement_point_form"):
            description = st.text_area(
                "What needs to be reviewed", value=point["description"]
            )
            completion_date = st.date_input(
                "Completion date",
                value=date.fromisoformat(point["completion_date"]),
            )
            col_save, col_cancel, col_delete = st.columns(3)
            with col_save:
                save = st.form_submit_button("💾 Save")
            with col_cancel:
                cancel = st.form_submit_button("Cancel")
            with col_delete:
                delete = st.form_submit_button("🗑️ Delete")

            if save:
                if not description.strip():
                    st.error("Description is required")
                else:
                    update_reinforcement_point(
                        point["id"], description.strip(), completion_date
                    )
                    st.success("Point updated")
                    clear_edit()
                    st.rerun()
            if cancel:
                clear_edit()
                st.rerun()
            if delete:
                delete_reinforcement_point(point["id"])
                st.success("Point deleted")
                clear_edit()
                st.rerun()


# -----------------------------------------------------------------------------
# Completed points toggle
# -----------------------------------------------------------------------------
show_completed = st.toggle("Show completed", value=False)
if show_completed:
    st.subheader("Completed reinforcement points")
    completed_points = [
        p for p in get_reinforcement_points(include_completed=True) if p["status"] == "Complete"
    ]
    if not completed_points:
        st.info("No completed reinforcement points yet.")
    else:
        for point in completed_points:
            with st.container(border=True):
                col_status, col_main = st.columns([1, 5])
                with col_status:
                    st.markdown(f"**{status_badge(point['status'])}**")
                with col_main:
                    st.markdown(f"**{point['resource_name']}**")
                    st.markdown(point["description"])
                    st.caption(f"Created: {point['created_at'][:10]}")


# -----------------------------------------------------------------------------
# Log reinforcement session
# -----------------------------------------------------------------------------
st.subheader("Log reinforcement session")

if not active_points:
    st.info("Create an active reinforcement point before logging a session.")
else:
    point_options = {
        f"{p['resource_name']}: {p['description'][:60]}{'...' if len(p['description']) > 60 else ''}": p["id"]
        for p in active_points
    }
    with st.form("create_reinforcement_session_form"):
        selected_labels = st.multiselect(
            "Reinforcement points", options=list(point_options.keys())
        )
        hours = st.number_input(
            "Hours", min_value=0.0, max_value=24.0, value=1.0, step=0.5
        )
        note = st.text_input("Note (optional)")
        submitted = st.form_submit_button("✅ Log session")
        if submitted:
            if not selected_labels:
                st.error("Select at least one reinforcement point")
            elif hours <= 0:
                st.error("Hours must be greater than 0")
            else:
                point_ids = [point_options[label] for label in selected_labels]
                create_reinforcement_session(point_ids, hours, note.strip())
                st.success("Reinforcement session logged")
                clear_edit()
                st.rerun()


# -----------------------------------------------------------------------------
# Recent reinforcement sessions
# -----------------------------------------------------------------------------
st.subheader("Recent reinforcement sessions")

sessions = get_reinforcement_sessions(limit=10)
if not sessions:
    st.info("No reinforcement sessions logged yet.")
else:
    for session in sessions:
        with st.container(border=True):
            col_main, col_actions = st.columns([5, 1])
            with col_main:
                st.markdown(
                    f"**{session['date']}** — {session['hours']:.1f} h across "
                    f"{session['point_count']} point(s)"
                )
                if session["note"]:
                    st.caption(session["note"])
            with col_actions:
                if st.button("Delete", key=f"delete_session_{session['id']}"):
                    st.session_state.delete_session_id = session["id"]
                    st.rerun()

if st.session_state.delete_session_id:
    session_id = st.session_state.delete_session_id
    st.warning("This will delete the reinforcement session and its linked points.")
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Yes, delete session"):
            delete_reinforcement_session(session_id)
            st.success("Session deleted")
            clear_edit()
            st.rerun()
    with col_cancel:
        if st.button("Cancel"):
            clear_edit()
            st.rerun()
