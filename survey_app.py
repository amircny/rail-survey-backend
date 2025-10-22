# survey_app.py — final (syntax-checked)
import os, json, requests, streamlit as st
from pathlib import Path
import os
import streamlit as st  # اگر بالاتر import کردی، همین کافیه

st.set_page_config(
    page_title="پرسشنامه سفر",
    menu_items={"Get help": None, "Report a bug": None, "About": None}
)

st.markdown("""
<style>
#MainMenu {visibility:hidden;}   /* منوی سه‌نقطه */
header {visibility:hidden;}      /* نوار بالایی و آیکون گیت‌هاب */
footer {visibility:hidden;}      /* فوتر استریم‌لیت */
</style>
""", unsafe_allow_html=True)
#.............................................................................
API = os.getenv("SURVEY_API", "http://localhost:8000")

#st.set_page_config(page_title="Project Survey", page_icon="📋", layout="centered")
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    direction: rtl;
    text-align: right;
    font-family: "Vazirmatn", "IRANSans", Tahoma, sans-serif;
}

h1, h2, h3, h4, h5, h6, p, label, span, div {
    direction: rtl;
    text-align: right;
}

/* دکمه‌ها و ورودی‌ها */
button, [data-testid="stTextInput"], [data-testid="stTextArea"] {
    direction: rtl !important;
    text-align: right !important;
}

/* شماره سؤال در سمت راست */
.q-index {
    right: 0 !important;
    left: auto !important;
}
</style>
""", unsafe_allow_html=True)

# CSS
CSS_PATH = os.path.join("assets", "style.css")
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Hero banner
ASSETS = Path(__file__).parent / "assets"

def find_img(name_candidates):
    for n in name_candidates:
        p = ASSETS / n
        if p.exists(): return str(p)
    return None

banner = find_img(["header.png","header.jpg","header.jpeg"])
icons  = find_img(["categories.png","categories.jpg","categories.jpeg"])

# tighter spacing + not full screen
st.markdown("""
<style>
.header-wrap img{border-radius:14px; box-shadow:0 6px 28px rgba(0,0,0,.25);}
.header-wrap { margin: 0 auto 8px; width: 80%; }  /* 80% page width; change to taste */
</style>
""", unsafe_allow_html=True)

left, center, right = st.columns([1,8,1])
with center:
    st.markdown('<div class="header-wrap">', unsafe_allow_html=True)
    if banner: st.image(banner, use_container_width=True)
    if icons:  st.image(icons,  use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if not banner or not icons:
    st.caption(f"Put images in: {ASSETS} (header.png/jpg & categories.png/jpg)")

# Header
st.markdown(
    """
<div class="app-header">
  <div class="app-title">🚆پرسشنامه بررسی الگوی سفر مسافران</div>
  <div class="app-subtitle">🚆
آینده حمل و نقل ریلی


 شرکت‌کنندگان عزیز،پیشاپیش از وقت و حمایت شما سپاسگزاریم

هدف از این نظرسنجی، شناسایی راهکارهایی برای بهبود حمل و نقل ریلی و تشویق مسافران بیشتر به استفاده از آن است. پرسشنامه، اهمیت و سطح رضایت از ۲۱ ویژگی مرتبط با بازار گردشگری را ارزیابی می‌کند.

این نظرسنجی توسط پروفسور فرانچسکا پالیارا از گروه مهندسی عمران، ساختمان و محیط زیست در دانشگاه ناپل فدریکو دوم و پروفسور کنسپسیون رومن گارسیا از گروه اقتصاد کاربردی در دانشگاه لاس پالماس د گران کاناریا برگزار می‌شود.

لطفاً توجه داشته باشید که نتایج کاملاً ناشناس هستند و داده‌ها منحصراً برای اهداف تحقیقاتی استفاده خواهند شد.</div>
</div>
""",
    unsafe_allow_html=True,
)

@st.cache_data(ttl=5)
def fetch_questions():
    r = requests.get(f"{API}/questions", timeout=8)
    r.raise_for_status()
    data = r.json().get("questions", [])
    data.sort(key=lambda q: (q.get("order", 0), q.get("id", 0)))
    return data

def submit_answers(payload: dict):
    r = requests.post(f"{API}/submit", json=payload, timeout=12)
    r.raise_for_status()
    return r.json()

# Load questions
try:
    questions = fetch_questions()
except Exception as e:
    st.error(f"Could not load questions from backend: {e}")
    st.stop()

if not questions:
    st.info("No questions available yet.")
    st.stop()

# Session
if "answers" not in st.session_state:
    st.session_state.answers = {}

# Meta row
st.markdown(
    f"""
<div class="meta-row">
  <span class="badge">سوال : {len(questions)}</span>
</div>
""",
    unsafe_allow_html=True,
)

# Form (styled via CSS on [data-testid="stForm"])
with st.form("survey_form"):
    for idx, q in enumerate(questions, start=1):
        qid   = q["id"]
        qtext = q["text"]
        qtype = q.get("type", "single")
        opts  = q.get("options", [])
        key_base = f"q_{qid}"

          # --- اگر Note وجود داشت، قبل از سؤال نشان بده ---
        note = (q.get("note") or "").strip()
        if note:
            st.markdown(
                f"""
                <div style="text-align:center; font-weight:700; font-size:1.05rem; margin:6px 0 4px;">
                    {note}
                </div>
                <div style="border-bottom:1px solid rgba(255,255,255,.2); margin:6px 0 8px;"></div>
                """,
                unsafe_allow_html=True,
            )

        # --- فقط یک بار سربرگ سؤال ---
        st.markdown(
            f"""
        <div class="question">
          <div class="q-index">{idx:02d}</div>
          <div class="q-text">{qtext}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # --- ویجت مطابق نوع سؤال ---
        if qtype == "single":
            labels = [o["label"] for o in opts]
            label_to_code = {o["label"]: o["code"] for o in opts}
            choice = st.radio(
                label="", options=labels if labels else ["(no options)"],
                key=key_base, horizontal=False, label_visibility="collapsed",
            )
            st.session_state.answers[qid] = label_to_code.get(choice, "")

        elif qtype == "multi":
            selected_codes = []
            for o in opts:          # ترتیب گزینه‌ها = بک‌اند
                code, label = o["code"], o["label"]
                chk = st.checkbox(label, key=f"{key_base}_{code}")
                if chk:
                    selected_codes.append(code)
            st.session_state[key_base] = selected_codes
            st.session_state.answers[qid] = selected_codes

        else:  # text
            txt = st.text_area(
                label="Your answer", key=f"{key_base}_text",
                height=110, label_visibility="collapsed",
            )
            st.session_state.answers[qid] = (txt or "").strip()

        # جداکننده‌ی بین سؤالات
        st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

    # دکمه‌ها باید داخل همین فرم باشند
    col_left, col_right = st.columns([1, 1])
    with col_left:
        reset = st.form_submit_button("Reset", type="secondary")
    with col_right:
        submitted = st.form_submit_button("Submit", use_container_width=True)


# Actions

if "reset" in locals() and reset:
    st.session_state.answers = {}
    st.rerun()

if "submitted" in locals() and submitted:
    missing = []
    for q in questions:
        ans = st.session_state.answers.get(q["id"])
        ok = (isinstance(ans, list) and len(ans) > 0) if q.get("type") == "multi" else bool(ans)
        if not ok:
            missing.append(q["text"])
   
    if missing:
        st.warning("Please answer all required questions:\n\n- " + "\n- ".join(missing))
    else:
        try:
            payload = {"answers": st.session_state.answers}
            res = submit_answers(payload)
            if res.get("ok"):
                
                st.markdown(
                    
                    """
                    
<div class="success-banner">
  ✅ Thank you! Your responses have been submitted.
</div>
""",
                    unsafe_allow_html=True,
                )
                st.session_state.answers = {}
            else:
                st.error(f"Backend did not confirm success: {json.dumps(res)}")
        except Exception as e:
            st.error(f"Submit failed: {e}")
