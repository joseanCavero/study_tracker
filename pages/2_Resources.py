import streamlit as st
from datetime import date
from db import (
    init_db,
    get_all_resources,
    get_resource,
    get_all_areas,
    create_resource,
    update_resource,
    delete_resource,
    get_resource_total_hours,
    get_resource_session_count,
    get_sessions_by_resource,
    create_session,
    get_resource_last_studied,
    RESOURCE_TYPES,
    RESOURCE_STATUSES,
)

st.set_page_config(page_title="Resources", page_icon="📖")

init_db()

st.title("📖 Resources")

# Handle navigation from other pages that set a pending resource id.
if "pending_resource_id" in st.session_state:
    pending = st.session_state.pop("pending_resource_id")
    st.query_params["resource_id"] = pending
    st.rerun()

query_params = st.query_params
selected_resource_id = query_params.get("resource_id")

if "log_resource_id" not in st.session_state:
    st.session_state.log_resource_id = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def select_resource(resource_id):
    st.query_params.update({"resource_id": resource_id})
    st.rerun()


def clear_selection():
    st.query_params.clear()
    st.rerun()


def log_hours_form(resource_id, key_suffix=""):
    today = date.today()
    with st.form(f"log_hours_form_{resource_id}_{key_suffix}"):
        session_date = st.date_input("Date", value=today, key=f"log_date_{resource_id}_{key_suffix}")
        hours = st.number_input("Hours", min_value=0.0, max_value=24.0, value=1.0, step=0.5, key=f"log_hours_{resource_id}_{key_suffix}")
        note = st.text_input("Note (optional)", key=f"log_note_{resource_id}_{key_suffix}")
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("✅ Log")
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state.log_resource_id = None
                st.rerun()
        if submitted:
            if hours <= 0:
                st.error("Hours must be greater than 0")
                return False
            create_session(resource_id, session_date, hours, note.strip())
            st.success("Study session logged")
            st.session_state.log_resource_id = None
            st.rerun()
            return True
    return False


# -----------------------------------------------------------------------------
# Detail view
# -----------------------------------------------------------------------------
if selected_resource_id:
    resource_id = int(selected_resource_id)
    resource = get_resource(resource_id)

    if not resource:
        st.error("Resource not found.")
        if st.button("Back to all resources"):
            clear_selection()
        st.stop()

    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.header(resource["name"])
    with col_right:
        if st.button("← Back to all resources"):
            clear_selection()

    total_hours = get_resource_total_hours(resource_id)
    session_count = get_resource_session_count(resource_id)
    last_studied = get_resource_last_studied(resource_id) or "Never"

    st.markdown(
        f"**Type:** {resource['type']} | **Status:** {resource['status']} | "
        f"**Area:** {resource['area_name']}"
    )
    if resource["author"]:
        st.markdown(f"**Author:** {resource['author']}")
    if resource["notes"]:
        st.markdown(f"**Notes:** {resource['notes']}")

    st.markdown(
        f"**{total_hours:.1f} hours** logged across **{session_count}** session(s). "
        f"Last studied: **{last_studied}**."
    )

    tab_log, tab_sessions, tab_edit, tab_delete = st.tabs(
        ["Log hours", "Session history", "Edit resource", "Delete resource"]
    )

    with tab_log:
        log_hours_form(resource_id, key_suffix="detail")

    with tab_sessions:
        sessions = get_sessions_by_resource(resource_id)
        if not sessions:
            st.info("No sessions logged yet.")
        else:
            data = [
                {
                    "Date": s["date"],
                    "Hours": s["hours"],
                    "Note": s["note"] or "",
                }
                for s in sessions
            ]
            st.dataframe(data, use_container_width=True, hide_index=True)

    with tab_edit:
        areas = get_all_areas()
        area_options = {a["name"]: a["id"] for a in areas}
        current_area_name = resource["area_name"]

        with st.form("edit_resource_form"):
            r_name = st.text_input("Name", value=resource["name"])
            r_area_name = st.selectbox(
                "Area", options=list(area_options.keys()), index=list(area_options.keys()).index(current_area_name)
            )
            r_type = st.selectbox("Type", RESOURCE_TYPES, index=RESOURCE_TYPES.index(resource["type"]))
            r_status = st.selectbox(
                "Status", RESOURCE_STATUSES, index=RESOURCE_STATUSES.index(resource["status"])
            )
            r_author = st.text_input("Author", value=resource["author"] or "")
            r_notes = st.text_area("Notes", value=resource["notes"] or "")
            col_save, col_cancel = st.columns(2)
            with col_save:
                submitted = st.form_submit_button("💾 Save")
            with col_cancel:
                if st.form_submit_button("Cancel"):
                    st.rerun()
            if submitted:
                if not r_name.strip():
                    st.error("Name is required")
                else:
                    update_resource(
                        resource_id,
                        r_name.strip(),
                        area_options[r_area_name],
                        r_type,
                        r_status,
                        r_author.strip(),
                        r_notes.strip(),
                    )
                    st.success("Resource updated")
                    st.rerun()

    with tab_delete:
        st.warning(f"This will delete the resource and its **{session_count}** logged session(s).")
        if st.button("Yes, delete"):
            delete_resource(resource_id)
            st.success("Resource deleted")
            clear_selection()

    st.stop()


# -----------------------------------------------------------------------------
# Main list view
# -----------------------------------------------------------------------------
areas = get_all_areas()
area_options = {"All areas": None}
area_options.update({a["name"]: a["id"] for a in areas})

with st.expander("Filters & sorting", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_area_name = st.selectbox("Area", list(area_options.keys()))
    with col2:
        status_filter = st.selectbox("Status", ["All statuses"] + RESOURCE_STATUSES)
    with col3:
        sort_by = st.selectbox("Sort by", ["Name", "Hours", "Last studied"])

area_id_filter = area_options[selected_area_name]
status = None if status_filter == "All statuses" else status_filter

resources = get_all_resources(area_id=area_id_filter, status=status)

if sort_by == "Hours":
    resources.sort(key=lambda r: (r.get("total_hours") or 0), reverse=True)
elif sort_by == "Last studied":
    resources.sort(key=lambda r: (r.get("last_studied") or ""), reverse=True)
else:
    resources.sort(key=lambda r: r["name"].lower())

if not resources:
    st.info("No resources found. Add one below.")
else:
    st.markdown(f"Showing **{len(resources)}** resource(s)")
    for r in resources:
        hours = r.get("total_hours") or 0
        last = r.get("last_studied") or "Never"
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.markdown(f"**{r['name']}**")
                st.caption(f"{r['type']} · {r['status']} · {r['area_name']}")
            with c2:
                st.markdown(f"{hours:.1f} h · {r.get('session_count') or 0} sessions")
                st.caption(f"Last studied: {last}")
            with c3:
                if st.button("Log hours", key=f"log_btn_{r['id']}"):
                    st.session_state.log_resource_id = r["id"]
                    st.rerun()
                if st.button("Open", key=f"open_res_{r['id']}"):
                    select_resource(r["id"])

            if st.session_state.log_resource_id == r["id"]:
                log_hours_form(r["id"], key_suffix="list")

with st.expander("➕ Add new resource"):
    areas = get_all_areas()
    if not areas:
        st.warning("Create an area of knowledge first.")
    else:
        area_options = {a["name"]: a["id"] for a in areas}
        with st.form("create_resource_form"):
            r_name = st.text_input("Resource name")
            r_area = st.selectbox("Area", list(area_options.keys()))
            r_type = st.selectbox("Type", RESOURCE_TYPES)
            r_status = st.selectbox("Status", RESOURCE_STATUSES)
            r_author = st.text_input("Author (optional)")
            r_notes = st.text_area("Notes (optional)")
            submitted = st.form_submit_button("Add resource")
            if submitted:
                if not r_name.strip():
                    st.error("Resource name is required")
                else:
                    new_id = create_resource(
                        r_name.strip(),
                        area_options[r_area],
                        r_type,
                        r_status,
                        r_author.strip(),
                        r_notes.strip(),
                    )
                    st.success("Resource added")
                    select_resource(new_id)
