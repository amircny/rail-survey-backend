# survey_app.py — clean full version

import os
from pathlib import Path
import json
import requests
import streamlit as st

# ---------------------- Page & Global Styles ----------------------
st.set_page_config(
    page_title="پرسشنامه سفر",
    page_icon="🚆",
    layout="centered",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

# Hide Streamlit chrome
st.markdown(
    """
<style>
#MainMenu {visibility:hidden;}
header {visibility:hidden;}
footer {visibility:hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# RTL + basic UI tweaks
st.markdown(
    """
<style>
html, body, [data-testid="stAppViewContainer"] {
  direction: rtl; text-align: right;
  font-family: "Vazirmatn", "IRANSans", Tahoma, sans-serif;
}
h1, h2, h3, h4, h5, h6, p, label, span, div {direction: rtl; text-align: right;}
button, [data-testid="stTextInput"], [data-testid="stTextArea"] {
  direction: rtl !important; text-align: right !important;
}
/* small helpers */
.meta-row .badge {
  display:inline-block;background:#0ea5e9;color:#fff;border-radius:999px;
  padding:.25rem .75rem;font-size:.9rem;margin:.25rem 0;
}
.question { position:relative;background:rgba(255,255,255,.03);
  border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:16px 18px;
  margin:14px 0; }
.q-index { position:absolute;top:-12px;right:12px;background:#22c55e;color:#fff;
  border-radius:18px;padding:4px 10px;font-weight:700;font-size:.9rem; }
.q-text { font-size:1rem; line-height:1.9; }
.separator { height:14px; }
.success-banner{
  margin:1rem 0;padding:14px 16px;border-radius:12px;background:#eafff4;color:#065f46;
  border:1px solid #10b981;
}
.header-wrap img{border-radius:14px; box-shadow:0 6px 28px rgba(0,0,0,.25);}
.header-wrap { margin: 0 auto 8px; width: 80%; }
</style>
""",
    unsafe_allow_html=True,
)

# Optional extra CSS file
CSS_PATH = os.path.join("assets", "style.css")
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------- Assets (optional) ----------------------
ASSETS = Path(__file__).parent / "assets"

def find_img(names):
    for n in names:
        p = ASSETS / n
        if p.exists():
            return str(p)
    return None

banner = find_img(["header.png", "header.jpg", "header.jpeg"])
icons  = find_img(["categories.png", "categories.jpg", "categories.jpeg"])

left, center, right = st.columns([1,8,1])
with center:
    st.markdown('<div class="header-wrap">', unsafe_allow_html=True)
    if banner:
        st.image(banner, use_container_width=True)
    if icons:
        st.image(icons, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------- API ----------------------
API = os.getenv("SURVEY_API", "http://localhost:8000")

@st.cache_data(ttl=5)
def fetch_questions():
    r = requests.get(f"{API}/questions", timeout=8)
    r.raise_for_status()
    data = r.json().get("questions", [])
    # keep backend order by "order" then id
    data.sort(key=lambda q: (q.get("order", 0), q.get("id", 0)))
    return data
def get_qtype(q: dict) -> str:
    """Return question type from either 'qtype' or 'type' (default: 'single')."""
    return q.get("qtype") or q.get("type") or "single"
def submit_answers(payload: dict):
    r = requests.post(f"{API}/submit", json=payload, timeout=12)
    r.raise_for_status()
    return r.json()

# ---------------------- Header Text ----------------------
st.markdown(
    """
<div class="app-header">
  <div class="app-title">🚆پرسشنامه بررسی الگوی سفر مسافران</div>
  <div class="app-subtitle">
  آینده حمل و نقل ریلی — شرکت‌کنندگان عزیز، پیشاپیش از وقت و حمایت شما سپاسگزاریم.
  این نظرسنجی تنها با اهداف پژوهشی و به‌صورت کاملاً ناشناس انجام می‌شود.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------- Load Questions ----------------------
try:
    questions = fetch_questions()
except Exception as e:
    st.error(f"Could not load questions from backend: {e}")
    st.stop()

if not questions:
    st.info("No questions available yet.")
    st.stop()

# ---------------------- Session State ----------------------
if "answers" not in st.session_state:
    st.session_state["answers"] = {}

# meta row (count)
st.markdown(
    f"""<div class="meta-row"><span class="badge">سوال : {len(questions)}</span></div>""",
    unsafe_allow_html=True,
)

# ---------------------- FORM ----------------------
with st.form("survey_form"):

    for idx, q in enumerate(questions, start=1):
        qid   = q.get("id")
        qtext = q.get("text", "")
        qtype = get_qtype(q)
        opts  = q.get("options", []) or []
        key_base = f"q_{qid}"

        # NOTE type: only display; no numbering; no answer
        if qtype == "note":
            if qtext:
                st.markdown(f"**{qtext}**")

            meta = (opts[0] if (isinstance(opts, list) and opts) else {}) or {}
            img_url = meta.get("image_url")
            caption = meta.get("caption")
            img_w   = meta.get("image_width")
            try:
                img_w = int(img_w) if img_w not in (None, "", 0, "0") else None
            except Exception:
                img_w = None

            if img_url:
                st.image(img_url, caption=caption or None, width=img_w)
            elif caption:
                st.caption(caption)

            st.markdown('<div class="separator"></div>', unsafe_allow_html=True)
            continue

        # Header for real question with numbering
        st.markdown(
            f"""
            <div class="question">
              <div class="q-index">{idx:02d}</div>
              <div class="q-text">{qtext}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Render widgets by type
        if qtype == "single":
            labels = [o.get("label", "") for o in opts]
            label_to_code = {o.get("label", ""): o.get("code", "") for o in opts}
            choice = st.radio(
                label="",
                options=labels if labels else ["(no options)"],
                key=key_base,
                horizontal=False,
                label_visibility="collapsed",
            )
            st.session_state["answers"][qid] = label_to_code.get(choice, "")

        elif qtype == "multi":
            selected = []
            for o in opts:
                code = o.get("code", "")
                label = o.get("label", "")
                chk = st.checkbox(label, key=f"{key_base}_{code}")
                if chk:
                    selected.append(code)
            st.session_state[key_base] = selected
            st.session_state["answers"][qid] = selected

        else:  # text
            txt = st.text_area(
                label="Your answer",
                key=f"{key_base}_text",
                height=110,
                label_visibility="collapsed",
            )
            st.session_state["answers"][qid] = (txt or "").strip()

        st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

    # Form buttons
    col_left, col_right = st.columns([1, 1])
    with col_left:
        reset = st.form_submit_button("Reset", type="secondary")
    with col_right:
        submitted = st.form_submit_button("Submit", use_container_width=True)

# ---------------------- Actions ----------------------
if reset:
    st.session_state["answers"] = {}
    st.rerun()

if submitted:
    # Validate (ignore "note")
    missing = []
    for q in questions:
        qtype = get_qtype(q)
        if qtype == "note":
            continue
        ans = st.session_state["answers"].get(q.get("id"))
        ok = (isinstance(ans, list) and len(ans) > 0) if qtype == "multi" else bool(ans)
        if not ok:
            missing.append(q.get("text", ""))

    if missing:
        st.warning("Please answer all required questions:\n\n- " + "\n- ".join(missing))
    else:
        try:
            payload = {"answers": st.session_state["answers"]}
            res = submit_answers(payload)
            if res.get("ok"):
                st.markdown(
                    """<div class="success-banner">✅ Thank you! Your responses have been submitted.</div>""",
                    unsafe_allow_html=True,
                )
                st.session_state["answers"] = {}
            else:
                st.error(f"Backend did not confirm success: {json.dumps(res, ensure_ascii=False)}")
        except Exception as e:
            st.error(f"Submit failed: {e}")
