import streamlit as st
import pandas as pd
from datetime import date
from db import (
    init_db,
    get_total_hours_all_time,
    get_hours_this_week,
    get_resources_in_progress_count,
    get_hours_per_area,
    get_hours_per_resource,
    get_hours_over_time,
    get_recent_sessions_last_weeks,
    get_all_areas,
)

st.set_page_config(page_title="Dashboard", page_icon="📊")

init_db()

st.title("📊 Dashboard")

# -----------------------------------------------------------------------------
# Quick stats
# -----------------------------------------------------------------------------
cols = st.columns(3)
with cols[0]:
    st.metric("Total hours (all time)", f"{get_total_hours_all_time():.1f}")
with cols[1]:
    st.metric("Hours this week", f"{get_hours_this_week():.1f}")
with cols[2]:
    st.metric("Resources in progress", get_resources_in_progress_count())

st.divider()

# -----------------------------------------------------------------------------
# Hours per area
# -----------------------------------------------------------------------------
st.subheader("Hours per area")
area_data = get_hours_per_area()
if area_data:
    df_areas = pd.DataFrame(area_data)
    df_areas = df_areas.rename(columns={"name": "Area", "total_hours": "Hours"})
    st.bar_chart(df_areas.set_index("Area")["Hours"], use_container_width=True)

    st.subheader("Progress toward 10,000-hour goal")
    for area in area_data:
        goal = area["goal_hours"] or 10000
        hours = area["total_hours"] or 0
        progress = min(hours / goal, 1.0) if goal > 0 else 0
        st.progress(progress, text=f"{area['name']}: {hours:.1f} / {goal:.0f} hours ({progress*100:.1f}%)")
else:
    st.info("No data yet. Log some study sessions to see charts.")

st.divider()

# -----------------------------------------------------------------------------
# Hours per resource
# -----------------------------------------------------------------------------
st.subheader("Hours per resource")
resource_data = get_hours_per_resource()
if resource_data:
    df_resources = pd.DataFrame(resource_data)
    df_resources = df_resources.rename(columns={"name": "Resource", "total_hours": "Hours"})
    st.bar_chart(df_resources.set_index("Resource")["Hours"].head(20), use_container_width=True)
else:
    st.info("No resources with logged hours yet.")

st.divider()

# -----------------------------------------------------------------------------
# Hours over time
# -----------------------------------------------------------------------------
st.subheader("Hours over time")
areas = get_all_areas()
area_options = {"All areas": None}
area_options.update({a["name"]: a["id"] for a in areas})

selected_area = st.selectbox("Area", list(area_options.keys()), key="time_area")
period = st.radio("Period", ["daily", "weekly"], horizontal=True, key="time_period")

hours_over_time = get_hours_over_time(
    period=period, area_id=area_options[selected_area]
)
if hours_over_time:
    df_time = pd.DataFrame(hours_over_time)
    df_time = df_time.rename(columns={"period": "Period", "total_hours": "Hours"})
    st.line_chart(df_time.set_index("Period")["Hours"], use_container_width=True)
else:
    st.info("No study sessions yet.")

st.divider()

# -----------------------------------------------------------------------------
# Recent activity
# -----------------------------------------------------------------------------
st.subheader("Recent activity (last 2 weeks)")
recent = get_recent_sessions_last_weeks(weeks=2)
if not recent:
    st.info("No study sessions in the last 2 weeks.")
else:
    for s in recent:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{s['date']}** — {s['hours']:.1f} h on *{s['resource_name']}*")
                if s["note"]:
                    st.caption(s["note"])
            with col2:
                if st.button("Open resource", key=f"recent_open_{s['id']}"):
                    st.session_state.pending_resource_id = s["resource_id"]
                    st.switch_page("pages/2_Resources.py")
