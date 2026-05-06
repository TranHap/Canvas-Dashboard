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
    while resp.links.get("next"):
        resp = requests.get(resp.links["next"]["url"], headers=HEADERS)
        resp.raise_for_status()
        data.extend(resp.json())
    return data

def api_single(path):
    url = f"{CANVAS_URL}/api/v1/{path}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

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
    return (dt - now).days

FILE_ICONS = {
    "File": "📄", "Page": "📝", "Assignment": "📋",
    "Quiz": "❓", "Discussion": "💬", "ExternalUrl": "🔗",
    "ExternalTool": "🔧", "SubHeader": "📌"
}

# --- AUTH CHECK ---
if not TOKEN:
    st.error("⚠️ Canvas token not found. Set `CANVAS_TOKEN` in Streamlit secrets.")
    st.stop()

with st.spinner("Loading your data..."):
    try:
        profile = api_single("users/self/profile")
    except Exception as e:
        st.error(f"Failed to connect to Canvas: {e}")
        st.stop()

    courses = api("users/self/courses?include[]=term&enrollment_state=active")
    spring26 = [c for c in courses if c.get("term", {}).get("name") == "Spring 2026" and c.get("name")]
    c_map = {c["id"]: c for c in courses}

    enrollments = api("users/self/enrollments?per_page=100")
    grade_map = {}
    for e in enrollments:
        g = e.get("grades", {}) or {}
        grade_map[e.get("course_id")] = {"score": g.get("current_score"), "grade": g.get("current_grade")}

    todo = api("users/self/todo")
    missing = api("users/self/missing_submissions")

# --- SIDEBAR ---
st.sidebar.image("https://vinuni.edu.vn/wp-content/uploads/2023/06/logo-vinuni.png", width=200)
st.sidebar.markdown("## 🎓 Canvas Dashboard")
st.sidebar.markdown(f"**{profile.get('name', 'Student')}**")
st.sidebar.caption("VinUni — Spring 2026")

st.sidebar.divider()

# Course quick links
st.sidebar.markdown("**Jump to course:**")
for c in spring26:
    st.sidebar.page_link(f"https://vinuni.instructure.com/courses/{c['id']}", label=c["name"], icon="🔗")

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📚 Courses", "📖 Lectures", "📅 Tasks"])

# ================================================
# TAB 1: OVERVIEW
# ================================================
with tab1:
    st.title("🎓 Overview")
    st.caption(f"Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Courses", len(spring26))
    with col2:
        graded = sum(1 for c in spring26 if grade_map.get(c["id"], {}).get("score") is not None)
        st.metric("Graded", f"{graded}/{len(spring26)}")
    with col3:
        st.metric("Upcoming", len(todo))
    with col4:
        st.metric("⚠️ Missing", len(missing), delta_color="inverse")

    st.divider()

    st.subheader("⚠️ Missing Submissions")
    if missing:
        mrows = []
        for m in missing:
            due = parse_date(m.get("due_at"))
            due_str = due.strftime("%b %d, %Y") if due else "—"
            mrows.append({
                "Assignment": m.get("name", "?"),
                "Course": c_map.get(m.get("course_id"), {}).get("name", f"Course {m.get('course_id')}"),
                "Due": due_str,
            })
        st.dataframe(pd.DataFrame(mrows), use_container_width=True, hide_index=True)
    else:
        st.success("All clear — no missing work 🎉")

# ================================================
# TAB 2: COURSES
# ================================================
with tab2:
    st.title("📚 Spring 2026 Courses")

    rows = []
    for c in spring26:
        g = grade_map.get(c["id"], {})
        score = g.get("score")
        grade = g.get("grade")
        rows.append({
            "Code": c.get("course_code", ""),
            "Course": c["name"],
            "Score": f"{score:.1f}%" if score else "—",
            "Grade": grade if grade else "—",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()

    # Detail for each course
    for c in spring26:
        with st.expander(f"📘 {c['name']}"):
            g = grade_map.get(c["id"], {})
            score = g.get("score")
            grade = g.get("grade")
            st.write(f"**Score:** {f'{score:.1f}%' if score else '—'} | **Grade:** {grade or '—'}")
            st.write(f"[🔗 Open in Canvas](https://vinuni.instructure.com/courses/{c['id']})")

# ================================================
# TAB 3: LECTURES (MODULES)
# ================================================
with tab3:
    st.title("📖 Course Lectures")

    if not spring26:
        st.info("No courses available.")
    else:
        # Pick a course
        course_names = [c["name"] for c in spring26]
        selected = st.selectbox("Select a course:", course_names, index=0)
        course = next(c for c in spring26 if c["name"] == selected)
        cid = course["id"]

        with st.spinner(f"Loading modules for {selected}..."):
            try:
                modules = api(f"courses/{cid}/modules?per_page=100")
            except:
                modules = []

        if not modules:
            st.info(f"No modules found in **{selected}**.")
        else:
            total_items = sum(m.get("items_count", 0) for m in modules)
            st.caption(f"{len(modules)} modules · {total_items} items")

            for m in modules:
                with st.expander(f"📁 {m['name']} ({m.get('items_count', 0)} items)"):
                    try:
                        items = api(f"courses/{cid}/modules/{m['id']}/items?per_page=100")
                    except:
                        st.warning("Could not load items")
                        continue

                    for item in items:
                        if not item.get("title"):
                            continue
                        itype = item["type"]
                        icon = FILE_ICONS.get(itype, "📎")
                        title = item["title"]

                        if itype == "File" and item.get("content_id"):
                            try:
                                file_data = api_single(f"files/{item['content_id']}")
                                fname = file_data.get("filename", "download")
                                download_url = file_data.get("url", "")
                                col_a, col_b = st.columns([4, 1])
                                col_a.markdown(f"{icon} **{title}**")
                                col_b.markdown(f"[⬇️ Download]({download_url})" if download_url else "")
                            except:
                                st.markdown(f"{icon} {title}")
                        elif itype == "Page" and item.get("page_url"):
                            try:
                                page_data = api_single(f"courses/{cid}/pages/{item['page_url']}")
                                body = page_data.get("body", "") or ""
                                st.markdown(f"{icon} **[{title}](https://vinuni.instructure.com/courses/{cid}/pages/{item['page_url']})**")
                                # Show preview
                                if body:
                                    body_clean = body[:2000]
                                    st.markdown(body_clean, unsafe_allow_html=True)
                                    if len(body) > 2000:
                                        st.caption(f"... + {len(body)-2000} more chars")
                            except:
                                st.markdown(f"{icon} **{title}**")
                        elif itype == "ExternalUrl":
                            url = item.get("external_url", "#")
                            st.markdown(f"{icon} [{title}]({url})")
                        elif itype in ("Assignment", "Quiz", "Discussion"):
                            st.markdown(f"{icon} **{title}**")
                        else:
                            st.markdown(f"{icon} {title}")

# ================================================
# TAB 4: TASKS & GRADES
# ================================================
with tab4:
    st.title("📅 Upcoming Tasks")

    if todo:
        trows = []
        for t in todo:
            a = t.get("assignment", {})
            due = parse_date(a.get("due_at"))
            due_str = due.strftime("%b %d, %Y %I:%M %p") if due else "No date"
            d = days_remaining(due)

            if d is not None:
                if d < 0:
                    urgency = "🔴 Overdue"
                elif d == 0:
                    urgency = "🟡 Due Today"
                elif d <= 3:
                    urgency = "🟠 Soon"
                elif d <= 7:
                    urgency = "🟢 This Week"
                else:
                    urgency = "⏳ Later"
            else:
                urgency = "📌"

            trows.append({
                "Task": a.get("name", "?"),
                "Course": a.get("course_name", ""),
                "Due": due_str,
                "Urgency": urgency,
            })

        st.dataframe(pd.DataFrame(trows), use_container_width=True, hide_index=True)
    else:
        st.info("No upcoming tasks — enjoy the calm ☕")

    st.divider()
    st.subheader("🏆 All Course Grades")
    all_g = []
    for c in courses:
        if not c.get("name"):
            continue
        g = grade_map.get(c["id"], {})
        score = g.get("score")
        grade = g.get("grade")
        all_g.append({
            "Course": c["name"],
            "Code": c.get("course_code", ""),
            "Term": c.get("term", {}).get("name", "?"),
            "Score": f"{score:.1f}%" if score else "—",
            "Grade": grade or "—",
        })
    st.dataframe(pd.DataFrame(all_g), use_container_width=True, hide_index=True)

st.sidebar.divider()
st.sidebar.markdown("Built with ❤️ by Forge · Canvas LMS")
