# admin_app.py — robust admin panel (Streamlit >= 1.30)
import os
import requests
import streamlit as st
API = os.getenv("SURVEY_API", "http://localhost:8000")

# API = "http://127.0.0.1:8000"  # آدرس بک‌اند FastAPI شما

st.set_page_config(page_title="Survey Admin", page_icon="🛠", layout="centered")
st.title("🛠 Survey Admin")


# ---------- Password Source (secrets -> ENV -> default) ----------
def get_admin_password() -> str:
    # 1) secrets.toml  (.streamlit/secrets.toml یا مسیر کاربر)
    try:
        val = st.secrets.get("ADMIN_PASSWORD", None)
        if val:
            return str(val)
    except Exception:
        pass
    # 2) متغیّر محیطی
    env_val = os.getenv("ADMIN_PASSWORD")
    if env_val:
        return env_val
    # 3) پیش‌فرض (فقط برای توسعه/لوکال)
    return "AmirStrongPass2025"


ADMIN_PASSWORD = get_admin_password()


# ---------- Session & Auth ----------
if "auth" not in st.session_state:
    st.session_state.auth = False

with st.form("login_form", clear_on_submit=False):
    pwd = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")
    if submitted:
        if pwd == ADMIN_PASSWORD:
            st.session_state.auth = True
            st.success("Logged in.")
            st.rerun()
        else:
            st.error("Wrong password. (Using secrets/env/default fallback)")


if not st.session_state.auth:
    st.stop()

# اختیاری: دکمه‌ی خروج
st.markdown("### Export")
st.link_button("⬇️ Download Excel", f"{API}/export_flat.xlsx")

with st.sidebar:
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

st.success("Logged in.")


# ---------- API helpers ----------
@st.cache_data(ttl=3)
def get_questions():
    r = requests.get(f"{API}/questions", timeout=6)
    r.raise_for_status()
    return r.json().get("questions", [])


def create_question(payload: dict):
    r = requests.post(f"{API}/question", json=payload, timeout=8)
    r.raise_for_status()
    return r.json()


def update_question(qid: int, payload: dict):
    r = requests.put(f"{API}/question/{qid}", json=payload, timeout=8)
    r.raise_for_status()
    return r.json()


def delete_question(qid: int):
    r = requests.delete(f"{API}/question/{qid}", timeout=8)
    r.raise_for_status()
    return r.json()


# ---------- Create new question ----------
st.subheader("Create new question")

col1, col2 = st.columns([2, 1])
with col1:
    new_text = st.text_input("Question text", key="new_text")
with col2:
    new_type = st.selectbox("Type", ["single", "multi", "text", "note"], key="new_type")

new_order = st.number_input("Order (integer)", value=999, step=1, key="new_order")

# فیلدهای مخصوص هر نوع
new_raw_opts = ""
new_note_img = ""
new_note_cap = ""
new_note_w   = 0

if new_type in ("single", "multi"):
    new_raw_opts = st.text_area(
        "Options (code:Label, comma separated)",
        placeholder="do:Dortmund Hbf, es:Essen Hbf, du:Düsseldorf Hbf",
        key="new_raw_opts",
    )
elif new_type == "note":
    st.markdown("**Note block (only UI — not stored as an answer)**")
    new_note_img = st.text_input("Image URL (optional)", key="new_note_img")
    new_note_cap = st.text_input("Caption (optional)", key="new_note_cap")
    new_note_w   = st.number_input("Image width (px)", min_value=0, value=600, step=50, key="new_note_w")

# ذخیره
if st.button("Save question"):
    try:
        # 1) ساخت options بر اساس نوع
        if new_type == "note":
            new_options = [{
                "image_url":  (new_note_img.strip() if new_note_img else ""),
                "caption":    (new_note_cap.strip() if new_note_cap else ""),
                "image_width": int(new_note_w) if new_note_w and new_note_w > 0 else None,
            }]
        elif new_type in ("single", "multi"):
            new_options = []
            raw = (new_raw_opts or "").strip()
            if raw:
                parts = [p.strip() for p in raw.split(",") if p.strip()]
                for i, chunk in enumerate(parts):
                    if ":" in chunk:
                        code, label = chunk.split(":", 1)
                        new_options.append({
                            "code": code.strip(),
                            "label": label.strip(),
                            "oorder": i,
                        })
        else:
            # text
            new_options = []

        # 2) فراخوانی API
        payload = {
            "text":   new_text,
            "qtype":  new_type,
            "qorder": int(new_order),
            "options": new_options,
        }
        res = create_question(payload)
        st.success(f"Saved. id={res.get('id')}")
        get_questions.clear()

    except Exception as e:
        st.error(f"Save failed: {e}")


# ---------- Existing questions ----------
st.subheader("Existing questions")

try:
    qs = get_questions()
except Exception as e:
    st.error(f"Load questions failed: {e}")
    qs = []

if not qs:
    st.info("No questions.")
else:
    for q in qs:
        with st.expander(f"[{q['id']}] {q['text']}"):
            t = st.text_input("Text", value=q["text"], key=f"t_{q['id']}")
            tp = st.selectbox(
                "Type", ["single", "multi", "text"],
                index=["single", "multi", "text"].index(q["type"]),
                key=f"type_{q['id']}"
            )
            ordr = st.number_input("Order", value=q.get("order", 0), step=1, key=f"ord_{q['id']}")

            cur = ", ".join([f"{o['code']}:{o['label']}" for o in q.get("options", [])])
            raw2 = st.text_area("Options (code:Label, comma separated)", value=cur, key=f"opts_{q['id']}")

            newopts = []
            if tp != "text" and raw2.strip():
                for i, chunk in enumerate([x.strip() for x in raw2.split(",") if x.strip()]):
                    if ":" in chunk:
                        code, label = chunk.split(":", 1)
                        newopts.append({"code": code.strip(), "label": label.strip(), "oorder": i})

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Update", key=f"upd_{q['id']}"):
                    try:
                        update_question(q["id"], {"text": t, "qtype": tp, "qorder": int(ordr), "options": newopts})
                        st.success("Updated.")
                        get_questions.clear()
                    except Exception as e:
                        st.error(f"Update failed: {e}")
            with c2:
                if st.button("Delete", key=f"del_{q['id']}"):
                    try:
                        delete_question(q["id"])
                        st.warning("Deleted.")
                        get_questions.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
