"""
app.py — Study Planner (Python + Streamlit)
Run: streamlit run app.py
"""

import hashlib
import os
import sys
from datetime import date, datetime, timedelta

import streamlit as st

# ── Make sure models/storage are importable when CWD differs (e.g. Render) ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import STATUSES, Subject, StudySession, Task
from storage import load_data, save_data

# ─────────────────────────────────────────────────────────────────────────────
# DATA LAYER  (session_state cache so disk is only hit once per rerun)
# ─────────────────────────────────────────────────────────────────────────────

def _init_data() -> None:
    """Load data from disk into session_state if not already loaded."""
    if "subjects" not in st.session_state:
        raw = load_data()
        st.session_state["subjects"] = raw["subjects"]   # List[Subject]
        st.session_state["tasks"]    = raw["tasks"]      # List[Task]
        st.session_state["sessions"] = raw["sessions"]   # List[StudySession]


def _commit() -> None:
    """Flush session_state back to disk."""
    save_data(
        st.session_state["subjects"],
        st.session_state["tasks"],
        st.session_state["sessions"],
    )


def _subjects()  -> list: return st.session_state["subjects"]
def _tasks()     -> list: return st.session_state["tasks"]
def _sessions()  -> list: return st.session_state["sessions"]

def _subject_names() -> list[str]:
    return [s.name for s in _subjects()]


# ─────────────────────────────────────────────────────────────────────────────
# FLASH MESSAGES
# ─────────────────────────────────────────────────────────────────────────────

def flash(msg: str, kind: str = "success") -> None:
    st.session_state["_flash"] = (msg, kind)


def show_flash() -> None:
    if "_flash" in st.session_state:
        msg, kind = st.session_state.pop("_flash")
        {"success": st.success, "error": st.error, "info": st.info}.get(kind, st.info)(msg)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG + GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Study Planner",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Stat cards ── */
.stat-card {
    background: linear-gradient(135deg,#1e2235,#252a3d);
    border: 1px solid #2e3557; border-radius:16px;
    padding:22px 20px 18px; position:relative; overflow:hidden;
    transition:transform .2s,box-shadow .2s;
}
.stat-card:hover{transform:translateY(-3px);box-shadow:0 12px 30px rgba(0,0,0,.4);}
.stat-card::before{
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    border-radius:16px 16px 0 0;
}
.stat-card.blue::before   {background:linear-gradient(90deg,#6c63ff,#48cae4);}
.stat-card.green::before  {background:linear-gradient(90deg,#43d97b,#0cb46c);}
.stat-card.red::before    {background:linear-gradient(90deg,#f25c54,#ff8a65);}
.stat-card.yellow::before {background:linear-gradient(90deg,#f9c74f,#f4a261);}
.stat-card.teal::before   {background:linear-gradient(90deg,#48cae4,#0096c7);}
.stat-card.purple::before {background:linear-gradient(90deg,#b48eff,#6c63ff);}
.stat-icon  {font-size:2rem;margin-bottom:10px;display:block;}
.stat-label {font-size:.72rem;font-weight:600;text-transform:uppercase;
             letter-spacing:1.2px;color:#7c84b0;margin-bottom:6px;}
.stat-value {font-size:2.2rem;font-weight:800;color:#e8eaf6;line-height:1;}
.stat-sub   {font-size:.75rem;color:#7c84b0;margin-top:6px;}

/* ── Hero banner ── */
.hero-banner{
    background:linear-gradient(135deg,#1a1d2e 0%,#252a42 50%,#1e2235 100%);
    border:1px solid #2e3557; border-radius:20px;
    padding:28px 32px; margin-bottom:24px; position:relative; overflow:hidden;
}
.hero-banner::after{
    content:'📚'; position:absolute; right:28px; top:50%;
    transform:translateY(-50%); font-size:5rem; opacity:.08;
}
.hero-greeting{font-size:1.6rem;font-weight:800;color:#e8eaf6;margin-bottom:4px;}
.hero-date    {font-size:.9rem;color:#7c84b0;}
.hero-quote   {font-size:.85rem;color:#9fa8da;margin-top:10px;font-style:italic;
               border-left:3px solid #6c63ff;padding-left:12px;}

/* ── Section titles ── */
.section-title{
    font-size:1.05rem;font-weight:700;color:#e8eaf6;
    margin:24px 0 14px; display:flex; align-items:center; gap:8px;
}
.section-title span{color:#6c63ff;}

/* ── Task pill cards ── */
.task-pill{
    background:#1e2235; border:1px solid #2e3557; border-radius:12px;
    padding:12px 16px; margin-bottom:8px;
    display:flex; align-items:center; gap:12px; transition:border-color .2s;
}
.task-pill:hover{border-color:#6c63ff;}
.task-pill-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;}
.dot-high  {background:#f25c54;box-shadow:0 0 6px #f25c54;}
.dot-medium{background:#f9c74f;box-shadow:0 0 6px #f9c74f;}
.dot-low   {background:#43d97b;box-shadow:0 0 6px #43d97b;}
.task-pill-title{font-size:.9rem;font-weight:600;color:#e8eaf6;flex:1;}
.task-pill-badge{
    font-size:.7rem;font-weight:700;padding:3px 10px;
    border-radius:20px;white-space:nowrap;
}
.badge-subj         {background:rgba(108,99,255,.18);color:#b0aaff;}
.badge-overdue      {background:rgba(242,92,84,.18); color:#f25c54;}
.badge-today        {background:rgba(249,199,79,.18);color:#f9c74f;}
.badge-status-done  {background:rgba(67,217,123,.18);color:#43d97b;}
.badge-status-prog  {background:rgba(72,202,228,.18);color:#48cae4;}
.badge-status-pend  {background:rgba(124,132,176,.18);color:#7c84b0;}
.task-pill-due{font-size:.75rem;color:#7c84b0;white-space:nowrap;}

/* ── Progress card ── */
.prog-card{
    background:linear-gradient(135deg,#1e2235,#252a3d);
    border:1px solid #2e3557; border-radius:16px;
    padding:18px 20px; margin-bottom:10px; transition:border-color .2s;
}
.prog-card:hover{border-color:#6c63ff;}
.prog-card-name{font-size:.95rem;font-weight:700;color:#e8eaf6;margin-bottom:10px;}
.prog-bar-bg  {background:#2e3557;border-radius:99px;height:8px;overflow:hidden;margin:4px 0 8px;}
.prog-bar-fill{height:100%;border-radius:99px;transition:width .5s ease;}
.prog-stats   {display:flex;gap:16px;flex-wrap:wrap;}
.prog-stat    {font-size:.75rem;color:#7c84b0;}
.prog-stat b  {color:#e8eaf6;}

/* ── Activity row ── */
.activity-row{
    display:flex;align-items:center;gap:10px;
    background:#1e2235;border:1px solid #2e3557;
    border-radius:12px;padding:10px 14px;margin-bottom:7px;
}
.activity-dot {width:8px;height:8px;border-radius:50%;background:#48cae4;flex-shrink:0;}
.activity-text{font-size:.82rem;color:#bfc8e8;flex:1;}
.activity-time{font-size:.72rem;color:#7c84b0;}

/* ── Session card ── */
.sess-card{
    background:#1e2235;border:1px solid #2e3557;border-radius:12px;
    padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;gap:14px;
    transition:border-color .2s;
}
.sess-card:hover{border-color:#6c63ff;}
.sess-icon{
    width:42px;height:42px;border-radius:10px;
    background:rgba(108,99,255,.15);display:flex;align-items:center;
    justify-content:center;font-size:1.1rem;flex-shrink:0;
}
.sess-body{flex:1;}
.sess-title{font-size:.95rem;font-weight:700;color:#e8eaf6;}
.sess-meta {font-size:.8rem;color:#7c84b0;margin-top:3px;}

/* ── Misc ── */
.stProgress > div > div > div > div{border-radius:99px;}
hr{margin:6px 0;border-color:#2e3250;}
div[data-testid="stForm"]{padding:12px 0 0 0;}
::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-track{background:#0f1117;}
::-webkit-scrollbar-thumb{background:#2e3557;border-radius:3px;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# BOOTSTRAP DATA
# ─────────────────────────────────────────────────────────────────────────────

_init_data()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────────────────────────────────────

st.sidebar.title("📚 Study Planner")
st.sidebar.markdown("---")

PAGES = {
    "🏠  Dashboard":      "dashboard",
    "✅  Tasks":          "tasks",
    "⏱  Study Sessions": "sessions",
    "📊  Progress":       "progress",
    "📖  Subjects":       "subjects",
}

if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"

for label, key in PAGES.items():
    if st.sidebar.button(
        label,
        use_container_width=True,
        type="primary" if st.session_state["page"] == key else "secondary",
    ):
        st.session_state["page"] = key
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"📅 {date.today().strftime('%A, %d %b %Y')}")

# Quick stats in sidebar
_t = _tasks()
_done = sum(1 for t in _t if t.status == "Completed")
_over = sum(1 for t in _t if t.is_overdue())
st.sidebar.markdown(f"""
<div style="font-size:.78rem;color:#7c84b0;padding:4px 0;">
  Tasks: <b style="color:#e8eaf6">{len(_t)}</b> &nbsp;·&nbsp;
  Done: <b style="color:#43d97b">{_done}</b> &nbsp;·&nbsp;
  Overdue: <b style="color:#f25c54">{_over}</b>
</div>
""", unsafe_allow_html=True)

page = st.session_state["page"]


# ─────────────────────────────────────────────────────────────────────────────
# ██████████████████████  DASHBOARD  ██████████████████████
# ─────────────────────────────────────────────────────────────────────────────

if page == "dashboard":
    show_flash()

    subjects  = _subjects()
    tasks     = _tasks()
    sessions  = _sessions()
    today_iso = date.today().isoformat()

    total_tasks    = len(tasks)
    done_tasks     = sum(1 for t in tasks if t.status == "Completed")
    inprog_tasks   = sum(1 for t in tasks if t.status == "In Progress")
    overdue_list   = [t for t in tasks if t.is_overdue()]
    today_tasks    = [t for t in tasks if t.due_date == today_iso and t.status != "Completed"]
    total_mins     = sum(s.duration_minutes for s in sessions)
    completion_pct = int(done_tasks / total_tasks * 100) if total_tasks else 0

    # Motivational quote (changes daily)
    QUOTES = [
        "The secret of getting ahead is getting started. — Mark Twain",
        "It always seems impossible until it's done. — Nelson Mandela",
        "Don't watch the clock; do what it does. Keep going. — Sam Levenson",
        "Success is the sum of small efforts, repeated day in and day out.",
        "Believe you can and you're halfway there. — Theodore Roosevelt",
        "Push yourself, because no one else is going to do it for you.",
        "Hard work beats talent when talent doesn't work hard.",
        "Study now so you can live the life you want later.",
    ]
    quote = QUOTES[int(hashlib.md5(today_iso.encode()).hexdigest(), 16) % len(QUOTES)]
    hour  = datetime.now().hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

    # ── Hero banner ──
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-greeting">{greeting}, Scholar! 🎓</div>
        <div class="hero-date">{date.today().strftime('%A, %d %B %Y')}</div>
        <div class="hero-quote">"{quote}"</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 6 stat cards ──
    card_defs = [
        ("blue",   "📋", "TOTAL TASKS",  str(total_tasks),             f"{done_tasks} completed"),
        ("green",  "✅", "COMPLETED",    str(done_tasks),              f"{completion_pct}% done"),
        ("red",    "⚠️", "OVERDUE",      str(len(overdue_list)),       "need attention"),
        ("yellow", "📅", "DUE TODAY",    str(len(today_tasks)),         "remaining today"),
        ("teal",   "⏱", "STUDY TIME",   f"{total_mins//60}h {total_mins%60}m", f"{len(sessions)} sessions"),
        ("purple", "📖", "SUBJECTS",     str(len(subjects)),           f"{inprog_tasks} in progress"),
    ]
    for col, (colour, icon, label, value, sub) in zip(st.columns(6), card_defs):
        col.markdown(f"""
        <div class="stat-card {colour}">
            <span class="stat-icon">{icon}</span>
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            <div class="stat-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SVG donut ring + recent activity ──
    ring_col, act_col = st.columns([1, 2])

    with ring_col:
        r, cx, cy, sw = 52, 70, 70, 12
        circ   = 2 * 3.14159 * r
        filled = circ * completion_pct / 100
        rc = "#43d97b" if completion_pct >= 75 else ("#f9c74f" if completion_pct >= 40 else "#f25c54")
        st.markdown(f"""
        <div style="text-align:center;padding:16px 0 8px;">
          <svg width="140" height="140" viewBox="0 0 140 140">
            <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#2e3557" stroke-width="{sw}"/>
            <circle cx="{cx}" cy="{cy}" r="{r}" fill="none"
                stroke="{rc}" stroke-width="{sw}"
                stroke-dasharray="{filled:.1f} {circ:.1f}"
                stroke-dashoffset="{circ/4:.1f}" stroke-linecap="round"/>
            <text x="{cx}" y="{cy-8}" text-anchor="middle"
                fill="#e8eaf6" font-size="22" font-weight="800"
                font-family="Inter,sans-serif">{completion_pct}%</text>
            <text x="{cx}" y="{cy+14}" text-anchor="middle"
                fill="#7c84b0" font-size="11"
                font-family="Inter,sans-serif">complete</text>
          </svg>
          <div style="font-size:.8rem;color:#7c84b0;margin-top:2px;">Overall Progress</div>
          <div style="display:flex;justify-content:center;gap:14px;margin-top:10px;flex-wrap:wrap;">
            <span style="font-size:.75rem;color:#43d97b;">✅ {done_tasks} done</span>
            <span style="font-size:.75rem;color:#48cae4;">🔄 {inprog_tasks} active</span>
            <span style="font-size:.75rem;color:#f25c54;">⚠️ {len(overdue_list)} overdue</span>
          </div>
        </div>""", unsafe_allow_html=True)

    with act_col:
        st.markdown('<div class="section-title">🕐 Recent Study Activity</div>', unsafe_allow_html=True)
        recent = sorted(sessions, key=lambda s: s.date, reverse=True)[:5]
        if recent:
            for s in recent:
                h, m = s.duration_minutes // 60, s.duration_minutes % 60
                dur  = f"{h}h {m}m" if h else f"{m}m"
                note = f" · {s.notes}" if s.notes else ""
                st.markdown(f"""
                <div class="activity-row">
                  <div class="activity-dot"></div>
                  <div class="activity-text"><b>{s.subject}</b>{note}</div>
                  <div class="activity-time">📅 {s.date} &nbsp;·&nbsp; ⏱ {dur}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="activity-row"><div class="activity-text" style="color:#7c84b0;">No sessions yet — start studying!</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Due today + Overdue ──
    def _pill(t: Task, badge: str) -> str:
        dot = {"High": "dot-high", "Medium": "dot-medium", "Low": "dot-low"}.get(t.priority, "dot-medium")
        bc  = "badge-overdue" if badge == "overdue" else "badge-today"
        bt  = "OVERDUE" if badge == "overdue" else "TODAY"
        sc  = {"Completed": "badge-status-done", "In Progress": "badge-status-prog"}.get(t.status, "badge-status-pend")
        return f"""
        <div class="task-pill">
          <div class="task-pill-dot {dot}"></div>
          <div class="task-pill-title">{t.title}</div>
          <span class="task-pill-badge badge-subj">{t.subject}</span>
          <span class="task-pill-badge {sc}">{t.status}</span>
          <span class="task-pill-badge {bc}">{bt}</span>
          <div class="task-pill-due">📅 {t.due_date}</div>
        </div>"""

    lc, rc2 = st.columns(2)
    with lc:
        st.markdown(f'<div class="section-title">📅 Due Today <span>({len(today_tasks)})</span></div>', unsafe_allow_html=True)
        if today_tasks:
            for t in today_tasks[:6]:
                st.markdown(_pill(t, "today"), unsafe_allow_html=True)
            if len(today_tasks) > 6:
                st.caption(f"+ {len(today_tasks)-6} more — see Tasks page")
        else:
            st.markdown('<div class="task-pill" style="justify-content:center;"><div class="task-pill-title" style="color:#43d97b;text-align:center;">🎉 Nothing due today — great job!</div></div>', unsafe_allow_html=True)

    with rc2:
        st.markdown(f'<div class="section-title">⚠️ Overdue Tasks <span>({len(overdue_list)})</span></div>', unsafe_allow_html=True)
        if overdue_list:
            for t in overdue_list[:6]:
                st.markdown(_pill(t, "overdue"), unsafe_allow_html=True)
            if len(overdue_list) > 6:
                st.caption(f"+ {len(overdue_list)-6} more — see Tasks page")
        else:
            st.markdown('<div class="task-pill" style="justify-content:center;"><div class="task-pill-title" style="color:#43d97b;text-align:center;">✅ No overdue tasks — you\'re on track!</div></div>', unsafe_allow_html=True)

    # ── Subject progress cards ──
    if subjects:
        st.markdown('<div class="section-title">📊 Subject Progress</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(subjects), 3))
        for idx, subj in enumerate(subjects):
            st_tasks = [t for t in tasks if t.subject == subj.name]
            s_total  = len(st_tasks)
            s_done   = sum(1 for t in st_tasks if t.status == "Completed")
            s_inprog = sum(1 for t in st_tasks if t.status == "In Progress")
            s_over   = sum(1 for t in st_tasks if t.is_overdue())
            s_mins   = sum(s.duration_minutes for s in sessions if s.subject == subj.name)
            s_pct    = int(s_done / s_total * 100) if s_total else 0
            bc       = "#43d97b" if s_pct >= 75 else ("#f9c74f" if s_pct >= 40 else "#f25c54")
            h, m     = s_mins // 60, s_mins % 60
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="prog-card">
                  <div class="prog-card-name">📗 {subj.name}</div>
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                    <span style="font-size:.78rem;color:#7c84b0;">{s_done}/{s_total} tasks done</span>
                    <span style="font-size:1rem;font-weight:800;color:{bc};">{s_pct}%</span>
                  </div>
                  <div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{s_pct}%;background:{bc};"></div></div>
                  <div class="prog-stats">
                    <div class="prog-stat">✅ Done <b>{s_done}</b></div>
                    <div class="prog-stat">🔄 Active <b>{s_inprog}</b></div>
                    <div class="prog-stat">⚠️ Overdue <b>{s_over}</b></div>
                    <div class="prog-stat">⏱ <b>{h}h {m}m</b></div>
                  </div>
                </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ██████████████████████  TASKS  ██████████████████████
# ─────────────────────────────────────────────────────────────────────────────

elif page == "tasks":
    show_flash()
    st.title("✅ Tasks")

    subj_names = _subject_names()
    tasks      = _tasks()

    # ── Add Task (expander) ──
    with st.expander("➕ Add New Task", expanded=not tasks):
        with st.form("form_add_task", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nt_title    = st.text_input("Title *", placeholder="e.g. Read chapter 5")
                nt_subject  = st.selectbox("Subject *", subj_names if subj_names else ["(add a subject first)"])
                nt_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
            with c2:
                nt_due    = st.date_input("Due Date *", value=date.today())
                nt_status = st.selectbox("Status", STATUSES)
                nt_notes  = st.text_area("Notes", placeholder="Optional notes...", height=98)

            if st.form_submit_button("💾 Save Task", type="primary"):
                if not nt_title.strip():
                    st.error("Title is required.")
                elif not subj_names:
                    st.error("Add a subject first (Subjects page).")
                else:
                    new_task = Task(
                        title    = nt_title.strip(),
                        subject  = nt_subject,
                        due_date = nt_due.isoformat(),
                        priority = nt_priority,
                        status   = nt_status,
                        notes    = nt_notes.strip(),
                    )
                    st.session_state["tasks"].append(new_task)
                    _commit()
                    flash(f'Task "{new_task.title}" added!', "success")
                    st.rerun()

    st.markdown("---")

    # ── Filters ──
    st.subheader("🔍 Filter & View Tasks")
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        f_status = st.selectbox("Status", ["All", "Pending", "In Progress", "Completed", "Overdue"], key="tf_status")
    with fc2:
        f_subj = st.selectbox("Subject", ["All Subjects"] + subj_names, key="tf_subj")
    with fc3:
        f_time = st.selectbox("Time Range", ["All Time", "Due Today", "This Week"], key="tf_time")

    today_iso = date.today().isoformat()
    week_end  = (date.today() + timedelta(days=6)).isoformat()

    view = list(tasks)
    if f_subj   != "All Subjects": view = [t for t in view if t.subject == f_subj]
    if f_status == "Overdue":      view = [t for t in view if t.is_overdue()]
    elif f_status != "All":        view = [t for t in view if t.status == f_status]
    if f_time   == "Due Today":    view = [t for t in view if t.due_date == today_iso]
    elif f_time == "This Week":    view = [t for t in view if today_iso <= t.due_date <= week_end]

    pw = {"High": 0, "Medium": 1, "Low": 2}
    view.sort(key=lambda t: (not t.is_overdue(), t.due_date, pw.get(t.priority, 1)))

    st.caption(f"Showing {len(view)} task(s)")
    st.markdown("---")

    if not view:
        st.info("📭 No tasks match your filters.")
    else:
        for t in view:
            od_flag = t.is_overdue()
            pi = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(t.priority, "⚪")
            si = {"Completed": "✅", "In Progress": "🔄", "Pending": "⏳"}.get(t.status, "⏳")
            with st.container():
                r1, r2 = st.columns([6, 2])
                with r1:
                    od_txt = " — ⚠️ **OVERDUE**" if od_flag else ""
                    st.markdown(
                        f"{pi} **{t.title}**{od_txt}  \n"
                        f"{si} `{t.status}` &nbsp;·&nbsp; 📚 `{t.subject}` "
                        f"&nbsp;·&nbsp; 📅 {t.due_date_display()}"
                        + (f"  \n📝 {t.notes}" if t.notes else "")
                    )
                with r2:
                    b1, b2, b3 = st.columns(3)
                    # Toggle complete
                    if b1.button(
                        "✅" if t.status != "Completed" else "↩️",
                        key=f"done_{t.task_id}", help="Toggle complete"
                    ):
                        for task in st.session_state["tasks"]:
                            if task.task_id == t.task_id:
                                task.status = "Completed" if task.status != "Completed" else "Pending"
                                break
                        _commit()
                        flash("Task status updated!", "success")
                        st.rerun()
                    # Edit
                    if b2.button("✏️", key=f"edit_{t.task_id}", help="Edit task"):
                        st.session_state["edit_task_id"] = t.task_id
                        st.rerun()
                    # Delete
                    if b3.button("🗑️", key=f"del_{t.task_id}", help="Delete task"):
                        st.session_state["tasks"] = [
                            x for x in st.session_state["tasks"] if x.task_id != t.task_id
                        ]
                        _commit()
                        flash(f'Task "{t.title}" deleted.', "success")
                        st.rerun()
                st.markdown("---")

    # ── Inline edit form ──
    if "edit_task_id" in st.session_state:
        eid  = st.session_state["edit_task_id"]
        etask = next((t for t in st.session_state["tasks"] if t.task_id == eid), None)
        if etask:
            st.markdown("---")
            st.subheader(f"✏️ Editing: {etask.title}")
            with st.form("form_edit_task"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_title = st.text_input("Title *", value=etask.title)
                    e_subj  = st.selectbox(
                        "Subject *",
                        subj_names if subj_names else [etask.subject],
                        index=(subj_names.index(etask.subject) if etask.subject in subj_names else 0),
                    )
                    e_prio  = st.selectbox(
                        "Priority",
                        ["High", "Medium", "Low"],
                        index=["High","Medium","Low"].index(etask.priority),
                    )
                with ec2:
                    try:
                        e_due_def = datetime.strptime(etask.due_date, "%Y-%m-%d").date()
                    except ValueError:
                        e_due_def = date.today()
                    e_due    = st.date_input("Due Date *", value=e_due_def)
                    e_status = st.selectbox(
                        "Status", STATUSES,
                        index=STATUSES.index(etask.status) if etask.status in STATUSES else 0,
                    )
                    e_notes  = st.text_area("Notes", value=etask.notes, height=98)

                sv, cn = st.columns(2)
                if sv.form_submit_button("💾 Save Changes", type="primary"):
                    if not e_title.strip():
                        st.error("Title is required.")
                    else:
                        for task in st.session_state["tasks"]:
                            if task.task_id == eid:
                                task.title    = e_title.strip()
                                task.subject  = e_subj
                                task.due_date = e_due.isoformat()
                                task.priority = e_prio
                                task.status   = e_status
                                task.notes    = e_notes.strip()
                                break
                        _commit()
                        del st.session_state["edit_task_id"]
                        flash(f'Task "{e_title.strip()}" updated!', "success")
                        st.rerun()
                if cn.form_submit_button("✖ Cancel"):
                    del st.session_state["edit_task_id"]
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# ██████████████████████  STUDY SESSIONS  ██████████████████████
# ─────────────────────────────────────────────────────────────────────────────

elif page == "sessions":
    show_flash()
    st.title("⏱ Study Sessions")

    subj_names = _subject_names()
    sessions   = _sessions()

    # ── Log session ──
    with st.expander("➕ Log New Session", expanded=not sessions):
        with st.form("form_add_session", clear_on_submit=True):
            sc1, sc2 = st.columns(2)
            with sc1:
                ss_subj = st.selectbox("Subject *", subj_names if subj_names else ["(add a subject first)"])
                ss_date = st.date_input("Date *", value=date.today())
            with sc2:
                ss_dur   = st.number_input("Duration (minutes) *", min_value=1, max_value=1440, value=60, step=5)
                ss_notes = st.text_area("Notes", placeholder="What did you study?", height=80)

            if st.form_submit_button("📝 Log Session", type="primary"):
                if not subj_names:
                    st.error("Add a subject first (Subjects page).")
                else:
                    new_sess = StudySession(
                        subject          = ss_subj,
                        date             = ss_date.isoformat(),
                        duration_minutes = int(ss_dur),
                        notes            = ss_notes.strip(),
                    )
                    st.session_state["sessions"].append(new_sess)
                    _commit()
                    flash(f"Logged {ss_dur} min of {ss_subj} on {ss_date}!", "success")
                    st.rerun()

    st.markdown("---")

    sessions_sorted = sorted(sessions, key=lambda s: s.date, reverse=True)

    if not sessions_sorted:
        st.info("⏱ No sessions logged yet. Start studying!")
    else:
        total_mins = sum(s.duration_minutes for s in sessions_sorted)
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Total Study Time", f"{total_mins//60}h {total_mins%60}m")
        mc2.metric("Total Sessions",   len(sessions_sorted))
        mc3.metric("Subjects Studied", len({s.subject for s in sessions_sorted}))

        st.markdown("---")
        st.subheader("Session History")

        # Subject filter
        sf_opt = ["All Subjects"] + subj_names
        sf_val = st.selectbox("Filter by Subject", sf_opt, key="sess_filter_subj")
        view_sess = sessions_sorted if sf_val == "All Subjects" else [
            s for s in sessions_sorted if s.subject == sf_val
        ]

        for s in view_sess:
            h, m  = s.duration_minutes // 60, s.duration_minutes % 60
            dur   = f"{h}h {m}m" if h else f"{m}m"
            sr1, sr2 = st.columns([6, 1])
            with sr1:
                st.markdown(f"""
                <div class="sess-card">
                  <div class="sess-icon">📖</div>
                  <div class="sess-body">
                    <div class="sess-title">{s.subject}</div>
                    <div class="sess-meta">📅 {s.date} &nbsp;·&nbsp; ⏱ {dur}{(' &nbsp;·&nbsp; 📝 ' + s.notes) if s.notes else ''}</div>
                  </div>
                </div>""", unsafe_allow_html=True)
            with sr2:
                if st.button("🗑️", key=f"delsess_{s.session_id}", help="Delete session"):
                    st.session_state["sessions"] = [
                        x for x in st.session_state["sessions"] if x.session_id != s.session_id
                    ]
                    _commit()
                    flash("Session deleted.", "success")
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# ██████████████████████  PROGRESS  ██████████████████████
# ─────────────────────────────────────────────────────────────────────────────

elif page == "progress":
    show_flash()
    st.title("📊 Progress Overview")

    subjects = _subjects()
    tasks    = _tasks()
    sessions = _sessions()

    if not subjects:
        st.info("📚 Add subjects and tasks to see your progress.")
    else:
        total_mins_all = sum(s.duration_minutes for s in sessions)
        all_done       = sum(1 for t in tasks if t.status == "Completed")
        overall_pct    = int(all_done / len(tasks) * 100) if tasks else 0

        oc1, oc2, oc3, oc4 = st.columns(4)
        oc1.metric("Overall Completion",  f"{overall_pct}%")
        oc2.metric("Total Study Time",    f"{total_mins_all//60}h {total_mins_all%60}m")
        oc3.metric("Total Tasks Done",    f"{all_done}/{len(tasks)}")
        oc4.metric("Subjects",            len(subjects))

        st.markdown("---")
        st.subheader("Per-Subject Breakdown")

        for subj in subjects:
            st_tasks = [t for t in tasks    if t.subject == subj.name]
            st_sess  = [s for s in sessions if s.subject == subj.name]
            s_total  = len(st_tasks)
            s_done   = sum(1 for t in st_tasks if t.status == "Completed")
            s_inprog = sum(1 for t in st_tasks if t.status == "In Progress")
            s_pend   = sum(1 for t in st_tasks if t.status == "Pending")
            s_over   = sum(1 for t in st_tasks if t.is_overdue())
            s_mins   = sum(s.duration_minutes for s in st_sess)
            s_pct    = int(s_done / s_total * 100) if s_total else 0
            bc       = "#43d97b" if s_pct >= 75 else ("#f9c74f" if s_pct >= 40 else "#f25c54")
            h, m     = s_mins // 60, s_mins % 60

            with st.container():
                pc1, pc2 = st.columns([3, 1])
                with pc1:
                    st.subheader(f"📗 {subj.name}")
                    st.progress(s_pct / 100, text=f"{s_pct}% complete")
                    sm1, sm2, sm3, sm4, sm5 = st.columns(5)
                    sm1.metric("Total",       s_total)
                    sm2.metric("Done",        s_done)
                    sm3.metric("In Progress", s_inprog)
                    sm4.metric("Overdue",     s_over)
                    sm5.metric("Study Time",  f"{h}h {m}m")
                with pc2:
                    st.markdown(f"""
| Status | Count |
|--------|-------|
| ✅ Done | {s_done} |
| 🔄 In Progress | {s_inprog} |
| ⏳ Pending | {s_pend} |
| ⚠️ Overdue | {s_over} |
| 📚 Sessions | {len(st_sess)} |
""")
                st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# ██████████████████████  SUBJECTS  ██████████████████████
# ─────────────────────────────────────────────────────────────────────────────

elif page == "subjects":
    show_flash()
    st.title("📖 Subjects")

    subjects = _subjects()
    tasks    = _tasks()
    sessions = _sessions()

    # ── Add subject ──
    with st.expander("➕ Add New Subject", expanded=not subjects):
        with st.form("form_add_subject", clear_on_submit=True):
            ns_name = st.text_input("Subject Name *", placeholder="e.g. Mathematics")
            if st.form_submit_button("➕ Add Subject", type="primary"):
                name = ns_name.strip()
                if not name:
                    st.error("Subject name is required.")
                elif any(s.name.lower() == name.lower() for s in subjects):
                    st.error(f'Subject "{name}" already exists.')
                else:
                    st.session_state["subjects"].append(Subject(name=name))
                    _commit()
                    flash(f'Subject "{name}" added!', "success")
                    st.rerun()

    st.markdown("---")
    st.subheader("Your Subjects")

    if not subjects:
        st.info("📚 No subjects yet. Add one above to get started!")
    else:
        for s in subjects:
            tc  = sum(1 for t in tasks    if t.subject == s.name)
            dc  = sum(1 for t in tasks    if t.subject == s.name and t.status == "Completed")
            sc  = sum(1 for ss in sessions if ss.subject == s.name)
            sm  = sum(ss.duration_minutes for ss in sessions if ss.subject == s.name)
            sh, smm = sm // 60, sm % 60

            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            with c1:
                st.markdown(f"### 📗 {s.name}")
                st.caption(f"ID: {s.subject_id}")
            with c2: st.metric("Tasks",      f"{dc}/{tc}")
            with c3: st.metric("Sessions",   sc)
            with c4: st.metric("Study Time", f"{sh}h {smm}m")
            with c5:
                if st.button("🗑️ Remove", key=f"delsubj_{s.subject_id}"):
                    st.session_state["confirm_delete_subject"] = s.subject_id
                    st.rerun()

            # Confirmation
            if st.session_state.get("confirm_delete_subject") == s.subject_id:
                st.warning(f"⚠️ Remove **{s.name}** and **all** its tasks & sessions? This cannot be undone.")
                yes_col, no_col = st.columns(2)
                if yes_col.button("✔️ Yes, delete everything", key=f"cyes_{s.subject_id}", type="primary"):
                    name_del = s.name
                    st.session_state["subjects"] = [
                        x for x in st.session_state["subjects"] if x.subject_id != s.subject_id
                    ]
                    st.session_state["tasks"] = [
                        t for t in st.session_state["tasks"] if t.subject != name_del
                    ]
                    st.session_state["sessions"] = [
                        ss for ss in st.session_state["sessions"] if ss.subject != name_del
                    ]
                    _commit()
                    del st.session_state["confirm_delete_subject"]
                    flash(f'Subject "{name_del}" and all related data deleted.', "success")
                    st.rerun()
                if no_col.button("✖ Cancel", key=f"cno_{s.subject_id}"):
                    del st.session_state["confirm_delete_subject"]
                    st.rerun()

            st.markdown("---")
