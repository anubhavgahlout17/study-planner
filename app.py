"""
app.py — Streamlit Study Planner
Run with: streamlit run app.py
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, date

import streamlit as st

# ── Persistence ───────────────────────────────────────────────────────────────

_local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
DATA_FILE = "/tmp/study_planner_data.json" if os.environ.get("RENDER") else _local


def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"subjects": [], "tasks": [], "sessions": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"subjects": [], "tasks": [], "sessions": []}


def _save(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_data() -> dict:
    """Load data into session_state cache so we only hit disk once per rerun."""
    if "data" not in st.session_state:
        st.session_state["data"] = _load()
    return st.session_state["data"]


def commit(data: dict) -> None:
    """Save data to disk and update the session_state cache."""
    _save(data)
    st.session_state["data"] = data


# ── Business logic helpers ────────────────────────────────────────────────────

def is_overdue(task: dict) -> bool:
    if task.get("status") == "Completed":
        return False
    try:
        return datetime.strptime(task["due_date"], "%Y-%m-%d").date() < date.today()
    except ValueError:
        return False


def compute_progress(data: dict) -> list:
    today = date.today()
    result = []
    for subj in data["subjects"]:
        name = subj["name"]
        subj_tasks = [t for t in data["tasks"] if t["subject"] == name]
        total  = len(subj_tasks)
        done   = sum(1 for t in subj_tasks if t["status"] == "Completed")
        inprog = sum(1 for t in subj_tasks if t["status"] == "In Progress")
        overdue = 0
        for t in subj_tasks:
            try:
                due = datetime.strptime(t["due_date"], "%Y-%m-%d").date()
                if due < today and t["status"] != "Completed":
                    overdue += 1
            except ValueError:
                pass
        mins = sum(s["duration_minutes"] for s in data["sessions"] if s["subject"] == name)
        pct  = int((done / total) * 100) if total else 0
        result.append({
            "name": name, "total": total, "done": done,
            "inprog": inprog, "overdue": overdue, "minutes": mins, "percent": pct,
        })
    return result


# ── Streamlit page config ─────────────────────────────────────────────────────

st.set_page_config(
    page_title="Study Planner",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Stat cards ── */
.stat-card {
    background: linear-gradient(135deg, #1e2235 0%, #252a3d 100%);
    border: 1px solid #2e3557;
    border-radius: 16px;
    padding: 22px 20px 18px;
    position: relative;
    overflow: hidden;
    transition: transform .2s, box-shadow .2s;
}
.stat-card:hover { transform: translateY(-3px); box-shadow: 0 12px 30px rgba(0,0,0,.4); }
.stat-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    border-radius: 16px 16px 0 0;
}
.stat-card.blue::before   { background: linear-gradient(90deg,#6c63ff,#48cae4); }
.stat-card.green::before  { background: linear-gradient(90deg,#43d97b,#0cb46c); }
.stat-card.red::before    { background: linear-gradient(90deg,#f25c54,#ff8a65); }
.stat-card.yellow::before { background: linear-gradient(90deg,#f9c74f,#f4a261); }
.stat-card.teal::before   { background: linear-gradient(90deg,#48cae4,#0096c7); }
.stat-card.purple::before { background: linear-gradient(90deg,#b48eff,#6c63ff); }

.stat-icon { font-size: 2rem; margin-bottom: 10px; display: block; }
.stat-label { font-size: .72rem; font-weight: 600; text-transform: uppercase;
              letter-spacing: 1.2px; color: #7c84b0; margin-bottom: 6px; }
.stat-value { font-size: 2.2rem; font-weight: 800; color: #e8eaf6; line-height: 1; }
.stat-sub   { font-size: .75rem; color: #7c84b0; margin-top: 6px; }

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(135deg, #1a1d2e 0%, #252a42 50%, #1e2235 100%);
    border: 1px solid #2e3557;
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-banner::after {
    content: '📚';
    position: absolute; right: 28px; top: 50%; transform: translateY(-50%);
    font-size: 5rem; opacity: .08;
}
.hero-greeting { font-size: 1.6rem; font-weight: 800; color: #e8eaf6; margin-bottom: 4px; }
.hero-date     { font-size: .9rem; color: #7c84b0; }
.hero-quote    { font-size: .85rem; color: #9fa8da; margin-top: 10px; font-style: italic;
                 border-left: 3px solid #6c63ff; padding-left: 12px; }

/* ── Section titles ── */
.section-title {
    font-size: 1.05rem; font-weight: 700; color: #e8eaf6;
    margin: 24px 0 14px;
    display: flex; align-items: center; gap: 8px;
}
.section-title span { color: #6c63ff; }

/* ── Task pill cards ── */
.task-pill {
    background: #1e2235;
    border: 1px solid #2e3557;
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: border-color .2s;
}
.task-pill:hover { border-color: #6c63ff; }
.task-pill-dot {
    width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}
.dot-high    { background: #f25c54; box-shadow: 0 0 6px #f25c54; }
.dot-medium  { background: #f9c74f; box-shadow: 0 0 6px #f9c74f; }
.dot-low     { background: #43d97b; box-shadow: 0 0 6px #43d97b; }
.task-pill-title { font-size: .9rem; font-weight: 600; color: #e8eaf6; flex: 1; }
.task-pill-badge {
    font-size: .7rem; font-weight: 700; padding: 3px 10px;
    border-radius: 20px; white-space: nowrap;
}
.badge-subj     { background: rgba(108,99,255,.18); color: #b0aaff; }
.badge-overdue  { background: rgba(242,92,84,.18);  color: #f25c54; }
.badge-today    { background: rgba(249,199,79,.18); color: #f9c74f; }
.badge-status-done  { background: rgba(67,217,123,.18); color: #43d97b; }
.badge-status-prog  { background: rgba(72,202,228,.18); color: #48cae4; }
.badge-status-pend  { background: rgba(124,132,176,.18); color: #7c84b0; }
.task-pill-due  { font-size: .75rem; color: #7c84b0; white-space: nowrap; }

/* ── Progress ring card ── */
.prog-card {
    background: linear-gradient(135deg, #1e2235 0%, #252a3d 100%);
    border: 1px solid #2e3557;
    border-radius: 16px;
    padding: 18px 20px;
    margin-bottom: 10px;
    transition: border-color .2s;
}
.prog-card:hover { border-color: #6c63ff; }
.prog-card-name { font-size: .95rem; font-weight: 700; color: #e8eaf6; margin-bottom: 10px; }
.prog-bar-bg {
    background: #2e3557; border-radius: 99px; height: 8px; overflow: hidden; margin: 4px 0 8px;
}
.prog-bar-fill { height: 100%; border-radius: 99px; transition: width .5s ease; }
.prog-stats { display: flex; gap: 16px; flex-wrap: wrap; }
.prog-stat  { font-size: .75rem; color: #7c84b0; }
.prog-stat b { color: #e8eaf6; }

/* ── Activity strip ── */
.activity-row {
    display: flex; align-items: center; gap: 10px;
    background: #1e2235; border: 1px solid #2e3557;
    border-radius: 12px; padding: 10px 14px; margin-bottom: 7px;
}
.activity-dot { width: 8px; height: 8px; border-radius: 50%; background: #48cae4; flex-shrink: 0; }
.activity-text { font-size: .82rem; color: #bfc8e8; flex: 1; }
.activity-time  { font-size: .72rem; color: #7c84b0; }

/* ── Progress bar (native Streamlit) ── */
.stProgress > div > div > div > div { border-radius: 99px; }

/* ── Task row divider ── */
hr { margin: 6px 0; border-color: #2e3250; }

/* ── Form spacing ── */
div[data-testid="stForm"] { padding: 12px 0 0 0; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0f1117; }
::-webkit-scrollbar-thumb { background: #2e3557; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar navigation ────────────────────────────────────────────────────────

st.sidebar.title("📚 Study Planner")
st.sidebar.markdown("---")

PAGES = {
    "🏠  Dashboard":       "dashboard",
    "✅  Tasks":           "tasks",
    "⏱  Study Sessions":  "sessions",
    "📊  Progress":        "progress",
    "📖  Subjects":        "subjects",
}

if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"

for label, key in PAGES.items():
    if st.sidebar.button(label, use_container_width=True,
                         type="primary" if st.session_state["page"] == key else "secondary"):
        st.session_state["page"] = key
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"Today: {date.today().strftime('%d %b %Y')}")

page = st.session_state["page"]

# ── Helper: inline notification state ────────────────────────────────────────

def flash(msg: str, kind: str = "success") -> None:
    """Store a one-shot message in session_state to show after rerun."""
    st.session_state["_flash"] = (msg, kind)


def show_flash() -> None:
    if "_flash" in st.session_state:
        msg, kind = st.session_state.pop("_flash")
        if kind == "success":
            st.success(msg)
        elif kind == "error":
            st.error(msg)
        else:
            st.info(msg)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD PAGE
# ══════════════════════════════════════════════════════════════════════════════

if page == "dashboard":
    show_flash()
    data         = get_data()
    tasks_all    = data["tasks"]
    sessions_all = data["sessions"]
    subjects_all = data["subjects"]

    today_str  = date.today().isoformat()
    today_name = date.today().strftime("%A")
    today_full = date.today().strftime("%d %B %Y")

    total_tasks    = len(tasks_all)
    done_tasks     = sum(1 for t in tasks_all if t["status"] == "Completed")
    inprog_tasks   = sum(1 for t in tasks_all if t["status"] == "In Progress")
    overdue_list   = [t for t in tasks_all if is_overdue(t)]
    today_list     = [t for t in tasks_all if t["due_date"] == today_str and t["status"] != "Completed"]
    total_mins     = sum(s["duration_minutes"] for s in sessions_all)
    completion_pct = int((done_tasks / total_tasks) * 100) if total_tasks else 0

    # ── Motivational quotes ───────────────────────────────────────────────────
    QUOTES = [
        "The secret of getting ahead is getting started. — Mark Twain",
        "It always seems impossible until it's done. — Nelson Mandela",
        "Don't watch the clock; do what it does. Keep going. — Sam Levenson",
        "Success is the sum of small efforts, repeated day in and day out.",
        "Believe you can and you're halfway there. — Theodore Roosevelt",
        "Push yourself, because no one else is going to do it for you.",
    ]
    quote = QUOTES[int(hashlib.md5(today_str.encode()).hexdigest(), 16) % len(QUOTES)]

    # ── Hero banner ───────────────────────────────────────────────────────────
    greeting = "Good morning" if datetime.now().hour < 12 else ("Good afternoon" if datetime.now().hour < 17 else "Good evening")
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-greeting">{greeting}, Scholar! 🎓</div>
        <div class="hero-date">{today_name}, {today_full}</div>
        <div class="hero-quote">"{quote}"</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stat cards row ────────────────────────────────────────────────────────
    cs = st.columns(6)
    card_data = [
        ("blue",   "📋", "TOTAL TASKS",   str(total_tasks),    f"{done_tasks} completed"),
        ("green",  "✅", "COMPLETED",     str(done_tasks),     f"{completion_pct}% done"),
        ("red",    "⚠️", "OVERDUE",       str(len(overdue_list)), "need attention"),
        ("yellow", "📅", "DUE TODAY",     str(len(today_list)), "remaining today"),
        ("teal",   "⏱", "STUDY TIME",    f"{total_mins//60}h {total_mins%60}m", f"{len(sessions_all)} sessions"),
        ("purple", "📖", "SUBJECTS",      str(len(subjects_all)), f"{inprog_tasks} in progress"),
    ]
    for col, (colour, icon, label, value, sub) in zip(cs, card_data):
        col.markdown(f"""
        <div class="stat-card {colour}">
            <span class="stat-icon">{icon}</span>
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            <div class="stat-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Overall completion ring (SVG) + activity strip ────────────────────────
    ring_col, act_col = st.columns([1, 2])

    with ring_col:
        # SVG donut ring
        r = 52; cx = 70; cy = 70; stroke_w = 12
        circumference = 2 * 3.14159 * r
        filled = circumference * completion_pct / 100
        ring_color = "#43d97b" if completion_pct >= 75 else ("#f9c74f" if completion_pct >= 40 else "#f25c54")
        st.markdown(f"""
        <div style="text-align:center; padding:16px 0 8px;">
            <svg width="140" height="140" viewBox="0 0 140 140">
                <circle cx="{cx}" cy="{cy}" r="{r}" fill="none"
                    stroke="#2e3557" stroke-width="{stroke_w}"/>
                <circle cx="{cx}" cy="{cy}" r="{r}" fill="none"
                    stroke="{ring_color}" stroke-width="{stroke_w}"
                    stroke-dasharray="{filled:.1f} {circumference:.1f}"
                    stroke-dashoffset="{circumference/4:.1f}"
                    stroke-linecap="round"/>
                <text x="{cx}" y="{cy - 8}" text-anchor="middle"
                    fill="#e8eaf6" font-size="22" font-weight="800" font-family="Inter,sans-serif">
                    {completion_pct}%
                </text>
                <text x="{cx}" y="{cy + 14}" text-anchor="middle"
                    fill="#7c84b0" font-size="11" font-family="Inter,sans-serif">
                    complete
                </text>
            </svg>
            <div style="font-size:.8rem;color:#7c84b0;margin-top:2px;">Overall Progress</div>
            <div style="display:flex;justify-content:center;gap:14px;margin-top:10px;flex-wrap:wrap;">
                <span style="font-size:.75rem;color:#43d97b;">✅ {done_tasks} done</span>
                <span style="font-size:.75rem;color:#48cae4;">🔄 {inprog_tasks} active</span>
                <span style="font-size:.75rem;color:#f25c54;">⚠️ {len(overdue_list)} overdue</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with act_col:
        # Recent study activity
        recent_sessions = sorted(sessions_all, key=lambda s: s["date"], reverse=True)[:5]
        st.markdown('<div class="section-title">🕐 Recent Study Activity</div>', unsafe_allow_html=True)
        if recent_sessions:
            for s in recent_sessions:
                h, m = s["duration_minutes"] // 60, s["duration_minutes"] % 60
                duration_str = f"{h}h {m}m" if h else f"{m}m"
                note_str = f" · {s['notes']}" if s.get("notes") else ""
                st.markdown(f"""
                <div class="activity-row">
                    <div class="activity-dot"></div>
                    <div class="activity-text">
                        <b>{s['subject']}</b>{note_str}
                    </div>
                    <div class="activity-time">📅 {s['date']} &nbsp;·&nbsp; ⏱ {duration_str}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="activity-row">
                <div class="activity-text" style="color:#7c84b0;">No sessions logged yet — start studying!</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Today's tasks + Overdue side by side ──────────────────────────────────
    left_col, right_col = st.columns(2)

    def _task_pill(t: dict, badge_type: str = "today") -> str:
        dot_cls  = {"High": "dot-high", "Medium": "dot-medium", "Low": "dot-low"}.get(t["priority"], "dot-medium")
        badge_cls = "badge-overdue" if badge_type == "overdue" else "badge-today"
        badge_txt = "OVERDUE" if badge_type == "overdue" else "TODAY"
        status_cls = {"Completed": "badge-status-done", "In Progress": "badge-status-prog"}.get(t["status"], "badge-status-pend")
        return f"""
        <div class="task-pill">
            <div class="task-pill-dot {dot_cls}"></div>
            <div class="task-pill-title">{t['title']}</div>
            <span class="task-pill-badge badge-subj">{t['subject']}</span>
            <span class="task-pill-badge {status_cls}">{t['status']}</span>
            <span class="task-pill-badge {badge_cls}">{badge_txt}</span>
            <div class="task-pill-due">📅 {t['due_date']}</div>
        </div>"""

    with left_col:
        st.markdown(f'<div class="section-title">📅 Due Today <span>({len(today_list)})</span></div>', unsafe_allow_html=True)
        if today_list:
            for t in today_list[:6]:
                st.markdown(_task_pill(t, "today"), unsafe_allow_html=True)
            if len(today_list) > 6:
                st.caption(f"+ {len(today_list)-6} more — go to Tasks")
        else:
            st.markdown("""
            <div class="task-pill" style="justify-content:center;">
                <div class="task-pill-title" style="color:#43d97b;text-align:center;">🎉 Nothing due today — great job!</div>
            </div>""", unsafe_allow_html=True)

    with right_col:
        st.markdown(f'<div class="section-title">⚠️ Overdue Tasks <span>({len(overdue_list)})</span></div>', unsafe_allow_html=True)
        if overdue_list:
            for t in overdue_list[:6]:
                st.markdown(_task_pill(t, "overdue"), unsafe_allow_html=True)
            if len(overdue_list) > 6:
                st.caption(f"+ {len(overdue_list)-6} more — go to Tasks")
        else:
            st.markdown("""
            <div class="task-pill" style="justify-content:center;">
                <div class="task-pill-title" style="color:#43d97b;text-align:center;">✅ No overdue tasks — you're on track!</div>
            </div>""", unsafe_allow_html=True)

    # ── Subject progress cards ────────────────────────────────────────────────
    if subjects_all:
        st.markdown('<div class="section-title">📊 Subject Progress</div>', unsafe_allow_html=True)
        progress_data = compute_progress(data)
        prog_cols = st.columns(min(len(progress_data), 3))
        for idx, p in enumerate(progress_data):
            bar_color = "#43d97b" if p["percent"] >= 75 else ("#f9c74f" if p["percent"] >= 40 else "#f25c54")
            h, m = p["minutes"] // 60, p["minutes"] % 60
            time_str = f"{h}h {m}m" if h else f"{m}m"
            with prog_cols[idx % 3]:
                st.markdown(f"""
                <div class="prog-card">
                    <div class="prog-card-name">📗 {p['name']}</div>
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                        <span style="font-size:.78rem;color:#7c84b0;">{p['done']}/{p['total']} tasks done</span>
                        <span style="font-size:1rem;font-weight:800;color:{bar_color};">{p['percent']}%</span>
                    </div>
                    <div class="prog-bar-bg">
                        <div class="prog-bar-fill" style="width:{p['percent']}%;background:{bar_color};"></div>
                    </div>
                    <div class="prog-stats">
                        <div class="prog-stat">✅ Done <b>{p['done']}</b></div>
                        <div class="prog-stat">🔄 Active <b>{p['inprog']}</b></div>
                        <div class="prog-stat">⚠️ Overdue <b>{p['overdue']}</b></div>
                        <div class="prog-stat">⏱ <b>{time_str}</b></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TASKS PAGE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "tasks":
    show_flash()
    data = get_data()
    subject_names = [s["name"] for s in data["subjects"]]

    st.title("✅ Tasks")

    # ── Add Task form ─────────────────────────────────────────────────────────
    with st.expander("➕ Add New Task", expanded=not data["tasks"]):
        with st.form("form_add_task", clear_on_submit=True):
            st.subheader("Add Task")
            col1, col2 = st.columns(2)
            with col1:
                new_title    = st.text_input("Title *", placeholder="e.g. Read chapter 5")
                new_subject  = st.selectbox("Subject *", subject_names if subject_names else ["(no subjects yet)"])
                new_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
            with col2:
                new_due    = st.date_input("Due Date *", value=date.today())
                new_status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
                new_notes  = st.text_area("Notes", placeholder="Optional notes...", height=100)

            submitted = st.form_submit_button("💾 Save Task", type="primary")
            if submitted:
                if not new_title.strip():
                    st.error("Title is required.")
                elif not subject_names:
                    st.error("Add a subject first (go to Subjects page).")
                else:
                    task = {
                        "task_id":    str(uuid.uuid4())[:8],
                        "title":      new_title.strip(),
                        "subject":    new_subject,
                        "due_date":   new_due.isoformat(),
                        "priority":   new_priority,
                        "status":     new_status,
                        "notes":      new_notes.strip(),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    data["tasks"].append(task)
                    commit(data)
                    flash(f'Task "{new_title.strip()}" added!', "success")
                    st.rerun()

    st.markdown("---")

    # ── Filters ───────────────────────────────────────────────────────────────
    st.subheader("🔍 Filter Tasks")
    fc1, fc2, fc3 = st.columns([2, 2, 2])
    with fc1:
        filter_status = st.selectbox(
            "Status",
            ["All", "Pending", "In Progress", "Completed", "Overdue"],
            key="task_filter_status",
        )
    with fc2:
        filter_subject_opts = ["All Subjects"] + subject_names
        filter_subject = st.selectbox("Subject", filter_subject_opts, key="task_filter_subject")
    with fc3:
        filter_time = st.selectbox(
            "Time Range",
            ["All Time", "Due Today", "This Week"],
            key="task_filter_time",
        )

    # ── Apply filters ─────────────────────────────────────────────────────────
    tasks_view = list(data["tasks"])
    today_str  = date.today().isoformat()
    week_end   = (date.today() + timedelta(days=6)).isoformat()

    if filter_subject != "All Subjects":
        tasks_view = [t for t in tasks_view if t["subject"] == filter_subject]
    if filter_status == "Overdue":
        tasks_view = [t for t in tasks_view if is_overdue(t)]
    elif filter_status != "All":
        tasks_view = [t for t in tasks_view if t["status"] == filter_status]
    if filter_time == "Due Today":
        tasks_view = [t for t in tasks_view if t["due_date"] == today_str]
    elif filter_time == "This Week":
        tasks_view = [t for t in tasks_view if today_str <= t["due_date"] <= week_end]

    # Sort: overdue first → due date → priority weight
    prio_w = {"High": 0, "Medium": 1, "Low": 2}
    tasks_view.sort(key=lambda t: (not is_overdue(t), t["due_date"], prio_w.get(t["priority"], 1)))

    st.caption(f"Showing {len(tasks_view)} task(s)")
    st.markdown("---")

    # ── Task list ─────────────────────────────────────────────────────────────
    if not tasks_view:
        st.info("📭 No tasks match your filters.")
    else:
        for t in tasks_view:
            overdue_flag = is_overdue(t)
            prio_icon    = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(t["priority"], "⚪")
            status_icon  = {"Completed": "✅", "In Progress": "🔄", "Pending": "⏳"}.get(t["status"], "⏳")

            with st.container():
                row1, row2 = st.columns([6, 2])
                with row1:
                    overdue_txt = " — ⚠️ **OVERDUE**" if overdue_flag else ""
                    st.markdown(
                        f"{prio_icon} **{t['title']}**{overdue_txt}  \n"
                        f"{status_icon} `{t['status']}` &nbsp;·&nbsp; 📚 `{t['subject']}` &nbsp;·&nbsp; 📅 {t['due_date']}"
                        + (f"  \n📝 {t['notes']}" if t.get("notes") else "")
                    )
                with row2:
                    btn_col1, btn_col2, btn_col3 = st.columns(3)

                    # Toggle complete
                    if btn_col1.button(
                        "✅" if t["status"] != "Completed" else "↩️",
                        key=f"done_{t['task_id']}",
                        help="Toggle complete",
                    ):
                        for task in data["tasks"]:
                            if task["task_id"] == t["task_id"]:
                                task["status"] = "Completed" if task["status"] != "Completed" else "Pending"
                                break
                        commit(data)
                        flash("Task updated!", "success")
                        st.rerun()

                    # Edit button — sets edit state
                    if btn_col2.button("✏️", key=f"edit_{t['task_id']}", help="Edit task"):
                        st.session_state["edit_task_id"] = t["task_id"]
                        st.rerun()

                    # Delete
                    if btn_col3.button("🗑️", key=f"del_{t['task_id']}", help="Delete task"):
                        data["tasks"] = [x for x in data["tasks"] if x["task_id"] != t["task_id"]]
                        commit(data)
                        flash(f'Task "{t["title"]}" deleted.', "success")
                        st.rerun()

                st.markdown("---")

    # ── Edit Task modal (rendered inline when active) ─────────────────────────
    if "edit_task_id" in st.session_state:
        edit_id   = st.session_state["edit_task_id"]
        edit_task = next((t for t in data["tasks"] if t["task_id"] == edit_id), None)
        if edit_task:
            st.markdown("---")
            st.subheader(f"✏️ Edit Task — {edit_task['title']}")
            with st.form("form_edit_task"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_title    = st.text_input("Title *",    value=edit_task["title"])
                    e_subject  = st.selectbox(
                        "Subject *",
                        subject_names if subject_names else [edit_task["subject"]],
                        index=(subject_names.index(edit_task["subject"]) if edit_task["subject"] in subject_names else 0),
                    )
                    e_priority = st.selectbox(
                        "Priority",
                        ["High", "Medium", "Low"],
                        index=["High", "Medium", "Low"].index(edit_task.get("priority", "Medium")),
                    )
                with ec2:
                    try:
                        e_due_default = datetime.strptime(edit_task["due_date"], "%Y-%m-%d").date()
                    except ValueError:
                        e_due_default = date.today()
                    e_due    = st.date_input("Due Date *", value=e_due_default)
                    e_status = st.selectbox(
                        "Status",
                        ["Pending", "In Progress", "Completed"],
                        index=["Pending", "In Progress", "Completed"].index(edit_task.get("status", "Pending")),
                    )
                    e_notes  = st.text_area("Notes", value=edit_task.get("notes", ""), height=100)

                save_col, cancel_col = st.columns(2)
                save_btn   = save_col.form_submit_button("💾 Save Changes", type="primary")
                cancel_btn = cancel_col.form_submit_button("✖ Cancel")

                if save_btn:
                    if not e_title.strip():
                        st.error("Title is required.")
                    else:
                        for task in data["tasks"]:
                            if task["task_id"] == edit_id:
                                task["title"]    = e_title.strip()
                                task["subject"]  = e_subject
                                task["due_date"] = e_due.isoformat()
                                task["priority"] = e_priority
                                task["status"]   = e_status
                                task["notes"]    = e_notes.strip()
                                break
                        commit(data)
                        del st.session_state["edit_task_id"]
                        flash(f'Task "{e_title.strip()}" updated!', "success")
                        st.rerun()

                if cancel_btn:
                    del st.session_state["edit_task_id"]
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STUDY SESSIONS PAGE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "sessions":
    show_flash()
    data = get_data()
    subject_names = [s["name"] for s in data["subjects"]]

    st.title("⏱ Study Sessions")

    # ── Log Session form ──────────────────────────────────────────────────────
    with st.expander("➕ Log New Session", expanded=not data["sessions"]):
        with st.form("form_add_session", clear_on_submit=True):
            st.subheader("Log Study Session")
            sc1, sc2 = st.columns(2)
            with sc1:
                s_subject  = st.selectbox("Subject *", subject_names if subject_names else ["(no subjects yet)"])
                s_date     = st.date_input("Date *", value=date.today())
            with sc2:
                s_duration = st.number_input("Duration (minutes) *", min_value=1, max_value=1440, value=60, step=5)
                s_notes    = st.text_area("Notes", placeholder="What did you study?", height=80)

            s_submitted = st.form_submit_button("📝 Log Session", type="primary")
            if s_submitted:
                if not subject_names:
                    st.error("Add a subject first (go to Subjects page).")
                else:
                    session = {
                        "session_id":       str(uuid.uuid4())[:8],
                        "subject":          s_subject,
                        "date":             s_date.isoformat(),
                        "duration_minutes": int(s_duration),
                        "notes":            s_notes.strip(),
                    }
                    data["sessions"].append(session)
                    commit(data)
                    flash(f"Logged {s_duration} min of {s_subject} on {s_date}!", "success")
                    st.rerun()

    st.markdown("---")

    sessions_all = sorted(data["sessions"], key=lambda s: s["date"], reverse=True)

    if not sessions_all:
        st.info("⏱ No sessions logged yet. Start studying!")
    else:
        total_mins = sum(s["duration_minutes"] for s in sessions_all)
        mc1, mc2 = st.columns(2)
        mc1.metric("Total Study Time", f"{total_mins // 60}h {total_mins % 60}m")
        mc2.metric("Total Sessions",   len(sessions_all))

        st.markdown("---")
        st.subheader("Session History")

        # Optional subject filter
        sf_opts = ["All Subjects"] + subject_names
        sf = st.selectbox("Filter by Subject", sf_opts, key="session_filter_subject")
        view_sessions = sessions_all if sf == "All Subjects" else [s for s in sessions_all if s["subject"] == sf]

        for s in view_sessions:
            sc_row1, sc_row2 = st.columns([5, 1])
            with sc_row1:
                st.markdown(
                    f"📖 **{s['subject']}** &nbsp;·&nbsp; 📅 {s['date']} &nbsp;·&nbsp; ⏱ {s['duration_minutes']} min"
                    + (f"  \n📝 {s['notes']}" if s.get("notes") else "")
                )
            with sc_row2:
                if st.button("🗑️", key=f"delsess_{s['session_id']}", help="Delete session"):
                    data["sessions"] = [x for x in data["sessions"] if x["session_id"] != s["session_id"]]
                    commit(data)
                    flash("Session deleted.", "success")
                    st.rerun()
            st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# PROGRESS PAGE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "progress":
    show_flash()
    data = get_data()
    st.title("📊 Progress Overview")

    if not data["subjects"]:
        st.info("📚 Add subjects and tasks to see your progress.")
    else:
        progress_data = compute_progress(data)
        total_mins_all = sum(s["duration_minutes"] for s in data["sessions"])
        all_tasks      = data["tasks"]
        total_done     = sum(1 for t in all_tasks if t["status"] == "Completed")
        overall_pct    = int((total_done / len(all_tasks)) * 100) if all_tasks else 0

        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("Overall Completion", f"{overall_pct}%")
        pc2.metric("Total Study Time",   f"{total_mins_all // 60}h {total_mins_all % 60}m")
        pc3.metric("Subjects",           len(data["subjects"]))

        st.markdown("---")
        st.subheader("Per-Subject Breakdown")

        for p in progress_data:
            with st.container():
                prog_col1, prog_col2 = st.columns([3, 1])
                with prog_col1:
                    st.subheader(p["name"])
                    st.progress(p["percent"] / 100, text=f"{p['percent']}% complete")

                    stat1, stat2, stat3, stat4, stat5 = st.columns(5)
                    stat1.metric("Total",       p["total"])
                    stat2.metric("Done",        p["done"])
                    stat3.metric("In Progress", p["inprog"])
                    stat4.metric("Overdue",     p["overdue"])
                    stat5.metric("Study Time",  f"{p['minutes']//60}h {p['minutes']%60}m")

                with prog_col2:
                    # Pie-style mini summary
                    pending = p["total"] - p["done"] - p["inprog"]
                    st.markdown(f"""
| Status | Count |
|--------|-------|
| ✅ Done | {p['done']} |
| 🔄 In Progress | {p['inprog']} |
| ⏳ Pending | {max(0, pending)} |
| ⚠️ Overdue | {p['overdue']} |
""")
                st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# SUBJECTS PAGE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "subjects":
    show_flash()
    data = get_data()

    st.title("📖 Subjects")

    # ── Add Subject form ──────────────────────────────────────────────────────
    with st.expander("➕ Add New Subject", expanded=not data["subjects"]):
        with st.form("form_add_subject", clear_on_submit=True):
            st.subheader("Add Subject")
            new_subj_name = st.text_input("Subject Name *", placeholder="e.g. Mathematics")
            subj_submitted = st.form_submit_button("➕ Add Subject", type="primary")
            if subj_submitted:
                name = new_subj_name.strip()
                if not name:
                    st.error("Subject name is required.")
                elif any(s["name"].lower() == name.lower() for s in data["subjects"]):
                    st.error(f'Subject "{name}" already exists.')
                else:
                    subject = {
                        "subject_id": str(uuid.uuid4())[:8],
                        "name": name,
                        "color": "white",
                    }
                    data["subjects"].append(subject)
                    commit(data)
                    flash(f'Subject "{name}" added!', "success")
                    st.rerun()

    st.markdown("---")
    st.subheader("Your Subjects")

    if not data["subjects"]:
        st.info("📚 No subjects yet. Add one above to get started!")
    else:
        for s in data["subjects"]:
            task_count = sum(1 for t in data["tasks"] if t["subject"] == s["name"])
            done_count = sum(1 for t in data["tasks"] if t["subject"] == s["name"] and t["status"] == "Completed")
            session_count = sum(1 for sess in data["sessions"] if sess["subject"] == s["name"])
            total_mins_subj = sum(
                sess["duration_minutes"] for sess in data["sessions"] if sess["subject"] == s["name"]
            )

            subj_col1, subj_col2, subj_col3, subj_col4, subj_col5 = st.columns([3, 1, 1, 1, 1])
            with subj_col1:
                st.markdown(f"### 📗 {s['name']}")
                st.caption(f"ID: {s['subject_id']}")
            with subj_col2:
                st.metric("Tasks", f"{done_count}/{task_count}")
            with subj_col3:
                st.metric("Sessions", session_count)
            with subj_col4:
                st.metric("Study Time", f"{total_mins_subj // 60}h {total_mins_subj % 60}m")
            with subj_col5:
                if st.button("🗑️ Remove", key=f"delsubj_{s['subject_id']}"):
                    st.session_state["confirm_delete_subject"] = s["subject_id"]
                    st.rerun()

            # Confirmation row
            if st.session_state.get("confirm_delete_subject") == s["subject_id"]:
                st.warning(
                    f"⚠️ Remove **{s['name']}** and **all** its tasks & sessions? This cannot be undone."
                )
                conf_col1, conf_col2 = st.columns(2)
                if conf_col1.button("✔️ Yes, delete everything", key=f"confirmyes_{s['subject_id']}", type="primary"):
                    name_del = s["name"]
                    data["subjects"] = [x for x in data["subjects"] if x["subject_id"] != s["subject_id"]]
                    data["tasks"]    = [t for t in data["tasks"]    if t["subject"] != name_del]
                    data["sessions"] = [ss for ss in data["sessions"] if ss["subject"] != name_del]
                    commit(data)
                    del st.session_state["confirm_delete_subject"]
                    flash(f'Subject "{name_del}" and all related data deleted.', "success")
                    st.rerun()
                if conf_col2.button("✖ Cancel", key=f"confirmno_{s['subject_id']}"):
                    del st.session_state["confirm_delete_subject"]
                    st.rerun()

            st.markdown("---")
