import streamlit as st
from db import init_db, get_total_hours_all_time, get_hours_this_week, get_resources_in_progress_count, get_hours_per_area

st.set_page_config(page_title="Home", page_icon="📚")

init_db()

st.title("📚 Study Tracker")

st.markdown(
    """
    Track your study progress across books, courses, videos, articles, and more.
    Organize everything by **areas of knowledge**, log study sessions, and see
    simple dashboards of where your time is going.
    """
)

st.subheader("Quick overview")

cols = st.columns(3)
with cols[0]:
    st.metric("Total hours studied", f"{get_total_hours_all_time():.1f}")
with cols[1]:
    st.metric("Hours this week", f"{get_hours_this_week():.1f}")
with cols[2]:
    st.metric("Resources in progress", get_resources_in_progress_count())

st.subheader("Progress toward 10,000-hour goal")

area_progress = get_hours_per_area()
if area_progress:
    for area in area_progress:
        goal = area["goal_hours"] or 10000
        hours = area["total_hours"] or 0
        progress = min(hours / goal, 1.0) if goal > 0 else 0
        st.progress(progress, text=f"{area['name']}: {hours:.1f} / {goal:.0f} hours ({progress*100:.1f}%)")
else:
    st.info("No areas yet. Create your first area of knowledge to start tracking progress.")
