# Canvas Student Dashboard

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

# --- CONFIG ---
st.set_page_config(page_title="🎓 Canvas Dashboard", layout="wide", page_icon="🎓")

CANVAS_URL = st.secrets.get("CANVAS_URL", "https://vinuni.instructure.com")
TOKEN = st.secrets.get("CANVAS_TOKEN", "")

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# --- HELPERS ---

def api(path):
    url = f"{CANVAS_URL}/api/v1/{path}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    # follow pagination
    while resp.links.get("next"):
        resp = requests.get(resp.links["next"]["url"], headers=HEADERS)
        resp.raise_for_status()
        data.extend(resp.json())
    return data

def parse_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except:
        return None

def days_remaining(dt):
    if not dt:
        return None
    now = datetime.now(timezone.utc)
    diff = (dt - now).days
    return diff

# --- SIDEBAR ---
st.sidebar.image("https://vinuni.edu.vn/wp-content/uploads/2023/06/logo-vinuni.png", width=200)
st.sidebar.markdown("## 🎓 Canvas Dashboard")
st.sidebar.markdown("**VinUni — Spring 2026**")
st.sidebar.divider()

if not TOKEN:
    st.error("⚠️ Canvas token not found. Set `CANVAS_TOKEN` in Streamlit secrets.")
    st.stop()

with st.spinner("Loading your data..."):
    # --- PROFILE ---
    try:
        profile = api("users/self/profile")
        st.sidebar.success(f"👤 {profile.get('name', 'Student')}")
        st.sidebar.caption(f"📧 {profile.get('primary_email', '')}")
    except Exception as e:
        st.error(f"Failed to connect to Canvas: {e}")
        st.stop()

    # --- COURSES ---
    courses = api("users/self/courses?include[]=term&enrollment_state=active")
    current_term = "Spring 2026"
    current_courses = [c for c in courses if c.get("term", {}).get("name") == current_term]
    
    # --- ENROLLMENTS (for grades) ---
    enrollments = api("users/self/enrollments?per_page=100")
    grade_map = {}
    for e in enrollments:
        cid = e.get("course_id")
        g = e.get("grades", {}) or {}
        grade_map[cid] = {
            "score": g.get("current_score"),
            "grade": g.get("current_grade"),
        }

    # --- TODO ---
    todo = api("users/self/todo")

    # --- MISSING ---
    missing = api("users/self/missing_submissions")

# ================================================
# DASHBOARD
# ================================================

st.title("🎓 Student Dashboard")
st.caption(f"Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")

# --- TOP ROW: STATS ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Active Courses", len(current_courses))
with col2:
    graded = [c for c in current_courses if grade_map.get(c["id"], {}).get("score") is not None]
    st.metric("Graded Courses", f"{len(graded)}/{len(current_courses)}")
with col3:
    st.metric("Upcoming Tasks", len(todo))
with col4:
    st.metric("⚠️ Missing Submissions", len(missing), delta_color="inverse")

st.divider()

# --- COURSES TABLE ---
st.subheader("📚 This Semester's Courses")

course_rows = []
for c in current_courses:
    cid = c["id"]
    g = grade_map.get(cid, {})
    score = g.get("score")
    grade = g.get("grade")
    
    course_rows.append({
        "Code": c.get("course_code", ""),
        "Course": c["name"],
        "Score": f"{score:.1f}%" if score is not None else "—",
        "Grade": grade if grade else "—",
        "Status": "✅ Active" if c.get("workflow_state") == "available" else "⏳",
    })

df_courses = pd.DataFrame(course_rows)
st.dataframe(df_courses, use_container_width=True, hide_index=True)

st.divider()

# --- MISSING SUBMISSIONS ---
st.subheader("⚠️ Missing Submissions")
if missing:
    cname_map = {c["id"]: c["name"] for c in courses}
    missing_rows = []
    for m in missing:
        due = parse_date(m.get("due_at"))
        due_str = due.strftime("%b %d, %Y %I:%M %p") if due else "No due date"
        days = days_remaining(due)
        days_str = f"{days} days ago" if days is not None and days < 0 else "Overdue" if days is not None else ""
        
        missing_rows.append({
            "Assignment": m.get("name", "Unknown"),
            "Course": cname_map.get(m.get("course_id", 0), f"Course {m.get('course_id', '?')}"),
            "Due": due_str,
            "Status": days_str if days_str else "⚠️ Missing",
        })
    df_missing = pd.DataFrame(missing_rows)
    st.dataframe(df_missing, use_container_width=True, hide_index=True)
else:
    st.success("No missing submissions! 🎉")

st.divider()

# --- TODO / UPCOMING ---
st.subheader("📅 Upcoming Tasks")
if todo:
    todo_rows = []
    for t in todo:
        a = t.get("assignment", {})
        due = parse_date(a.get("due_at"))
        due_str = due.strftime("%b %d, %Y %I:%M %p") if due else "No due date"
        days = days_remaining(due)
        
        if days is not None:
            if days < 0:
                urgency = "🔴 Overdue"
            elif days == 0:
                urgency = "🟡 Due Today"
            elif days <= 3:
                urgency = "🟠 Soon"
            elif days <= 7:
                urgency = "🟢 This Week"
            else:
                urgency = "⏳ Later"
        else:
            urgency = "📌"
        
        todo_rows.append({
            "Task": a.get("name", "Unknown"),
            "Course": a.get("course_name", ""),
            "Due": due_str,
            "Urgency": urgency,
        })
    df_todo = pd.DataFrame(todo_rows)
    st.dataframe(df_todo, use_container_width=True, hide_index=True)
else:
    st.info("No upcoming tasks — enjoy the calm before the storm. ☕")

st.divider()

# --- ALL COURSES (detailed grades) ---
st.subheader("🏆 All Course Grades")
all_grades = []
for c in courses:
    if not c.get("name"):
        continue
    cid = c["id"]
    g = grade_map.get(cid, {})
    score = g.get("score")
    grade = g.get("grade")
    term_name = c.get("term", {}).get("name", "Unknown")
    
    all_grades.append({
        "Course": c["name"],
        "Code": c.get("course_code", ""),
        "Term": term_name,
        "Score": f"{score:.1f}%" if score is not None else "—",
        "Grade": grade if grade else "—",
    })

df_grades = pd.DataFrame(all_grades)
st.dataframe(df_grades, use_container_width=True, hide_index=True)

st.sidebar.divider()
st.sidebar.markdown("Built with ❤️ by Forge · Powered by Canvas LMS")
