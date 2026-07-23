import streamlit as st
from db import (
    init_db,
    get_all_areas,
    get_area,
    create_area,
    update_area,
    delete_area,
    count_resources_in_area,
    get_area_total_hours,
    get_resources_by_area,
    reassign_resources_to_area,
    create_resource,
    RESOURCE_TYPES,
    RESOURCE_STATUSES,
)

st.set_page_config(page_title="Areas of Knowledge", page_icon="🧠")

init_db()

st.title("🧠 Areas of Knowledge")

query_params = st.query_params
selected_area_id = query_params.get("area_id")


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def select_area(area_id):
    st.query_params.update({"area_id": area_id})
    st.rerun()


def clear_selection():
    st.query_params.clear()
    st.rerun()


def area_card(area):
    resource_count = count_resources_in_area(area["id"])
    total_hours = get_area_total_hours(area["id"])
    goal = area["goal_hours"] or 10000
    progress = min(total_hours / goal, 1.0) if goal > 0 else 0

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{area['name']}**")
            if area["description"]:
                st.caption(area["description"])
            st.progress(progress, text=f"{total_hours:.1f} / {goal:.0f} hours ({progress*100:.1f}%)")
        with col2:
            st.markdown(f"Resources: **{resource_count}**")
            if st.button("Open", key=f"open_area_{area['id']}"):
                select_area(area["id"])


# -----------------------------------------------------------------------------
# Detail view
# -----------------------------------------------------------------------------
if selected_area_id:
    area_id = int(selected_area_id)
    area = get_area(area_id)

    if not area:
        st.error("Area not found.")
        if st.button("Back to all areas"):
            clear_selection()
        st.stop()

    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.header(area["name"])
    with col_right:
        if st.button("← Back to all areas"):
            clear_selection()

    if area["description"]:
        st.markdown(area["description"])

    total_hours = get_area_total_hours(area_id)
    goal = area["goal_hours"] or 10000
    progress = min(total_hours / goal, 1.0) if goal > 0 else 0
    st.progress(progress, text=f"{total_hours:.1f} / {goal:.0f} hours ({progress*100:.1f}%)")

    tab_edit, tab_resources, tab_add_resource, tab_delete = st.tabs(
        ["Edit area", "Resources in this area", "Add resource", "Delete area"]
    )

    with tab_edit:
        with st.form("edit_area_form"):
            name = st.text_input("Name", value=area["name"])
            description = st.text_area("Description", value=area["description"] or "")
            goal_hours = st.number_input(
                "Goal hours", min_value=0.0, value=float(area["goal_hours"]), step=100.0
            )
            col_save, col_cancel = st.columns(2)
            with col_save:
                submitted = st.form_submit_button("💾 Save")
            with col_cancel:
                if st.form_submit_button("Cancel"):
                    st.rerun()
            if submitted:
                if not name.strip():
                    st.error("Name is required")
                else:
                    update_area(area_id, name.strip(), description.strip(), goal_hours)
                    st.success("Area updated")
                    st.rerun()

    with tab_resources:
        resources = get_resources_by_area(area_id)
        if not resources:
            st.info("No resources in this area yet.")
        else:
            for r in resources:
                hours = r.get("total_hours") or 0
                last = r.get("last_studied") or "Never"
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{r['name']}**")
                        st.caption(f"{r['type']} · {r['status']} · {hours:.1f} h · last: {last}")
                    with c2:
                        if st.button("Open", key=f"open_res_{r['id']}"):
                            st.session_state.pending_resource_id = r["id"]
                            st.switch_page("pages/2_Resources.py")

    with tab_add_resource:
        with st.form("add_resource_form"):
            st.subheader("Add a resource to this area")
            r_name = st.text_input("Resource name")
            r_type = st.selectbox("Type", RESOURCE_TYPES)
            r_status = st.selectbox("Status", RESOURCE_STATUSES)
            r_author = st.text_input("Author (optional)")
            r_notes = st.text_area("Notes (optional)")
            submitted = st.form_submit_button("Add resource")
            if submitted:
                if not r_name.strip():
                    st.error("Resource name is required")
                else:
                    create_resource(
                        r_name.strip(), area_id, r_type, r_status, r_author.strip(), r_notes.strip()
                    )
                    st.success("Resource added")
                    st.rerun()

    with tab_delete:
        resource_count = count_resources_in_area(area_id)
        if resource_count == 0:
            st.warning("Are you sure you want to delete this area?")
            if st.button("Yes, delete"):
                delete_area(area_id)
                st.success("Area deleted")
                clear_selection()
        else:
            st.warning(
                f"This area has **{resource_count}** resource(s). Choose how to proceed:"
            )
            delete_option = st.radio(
                "Delete option",
                ["Delete all resources too", "Reassign resources to another area"],
                label_visibility="collapsed",
            )

            if delete_option == "Delete all resources too":
                if st.button("Confirm delete area and resources"):
                    delete_area(area_id)
                    st.success("Area and its resources deleted")
                    clear_selection()
            else:
                other_areas = [a for a in get_all_areas() if a["id"] != area_id]
                reassign_options = ["Create new area"] + [f"{a['name']} (#{a['id']})" for a in other_areas]
                reassign_map = {f"{a['name']} (#{a['id']})": a["id"] for a in other_areas}
                choice = st.selectbox("Reassign to", reassign_options)

                if choice == "Create new area":
                    new_area_name = st.text_input("New area name")
                    if st.button("Create area and reassign"):
                        if not new_area_name.strip():
                            st.error("New area name is required")
                        else:
                            new_id = create_area(new_area_name.strip())
                            reassign_resources_to_area(area_id, new_id)
                            delete_area(area_id)
                            st.success(f"Resources reassigned to '{new_area_name}'")
                            clear_selection()
                else:
                    new_area_id = reassign_map[choice]
                    if st.button("Reassign and delete area"):
                        reassign_resources_to_area(area_id, new_area_id)
                        delete_area(area_id)
                        st.success("Resources reassigned and area deleted")
                        clear_selection()

    st.stop()


# -----------------------------------------------------------------------------
# Main list view
# -----------------------------------------------------------------------------
areas = get_all_areas()

if not areas:
    st.info("No areas of knowledge yet. Create your first one below.")
else:
    for area in areas:
        area_card(area)

with st.expander("➕ Create new area", expanded=not areas):
    with st.form("create_area_form"):
        name = st.text_input("Name")
        description = st.text_area("Description (optional)")
        goal_hours = st.number_input(
            "Goal hours", min_value=0.0, value=10000.0, step=100.0
        )
        submitted = st.form_submit_button("Create area")
        if submitted:
            if not name.strip():
                st.error("Name is required")
            else:
                new_id = create_area(name.strip(), description.strip(), goal_hours)
                st.success("Area created")
                select_area(new_id)
