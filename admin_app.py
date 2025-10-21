# admin_app.py — Streamlit admin panel (fixed version)
import os
import json
import requests
import streamlit as st

# ------------------------------ Config ------------------------------
st.set_page_config(page_title="Survey Admin", layout="centered")
st.markdown(
    """
    <style>
    .stTextInput > div > div > input, .stTextArea textarea {
        direction: rtl; text-align: right;
    }
    .stNumberInput input { direction: ltr; }
    </style>
    """,
    unsafe_allow_html=True
)

API = os.getenv("SURVEY_API", "http://localhost:8000")
TYPE_CHOICES = ["single", "multi", "text", "note"]

# ------------------------------ Helpers ------------------------------

def get_qtype(q: dict) -> str:
    """Return question type from either 'qtype' or 'type' (default: 'single')."""
    return q.get("qtype") or q.get("type") or "single"

@st.cache_data(ttl=5)
def get_questions():
    r = requests.get(f"{API}/questions", timeout=10)
    r.raise_for_status()
    data = r.json().get("questions", [])
    # Sort order then id (just to be safe)
    data.sort(key=lambda q: (q.get("order", 0), q.get("id", 0)))
    return data

def create_question(payload: dict):
    r = requests.post(f"{API}/question", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()

def update_question(qid: int, payload: dict):
    r = requests.put(f"{API}/question/{qid}", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()

def delete_question(qid: int):
    r = requests.delete(f"{API}/question/{qid}", timeout=15)
    r.raise_for_status()
    return r.json()

def export_excel():
    r = requests.get(f"{API}/export.xlsx", timeout=30)
    r.raise_for_status()
    return r.content

# ------------------------------ UI: Export ------------------------------

st.title("Export")

col1, col2 = st.columns([1,4])
with col1:
    if st.button("⬇️ Download Excel"):
        try:
            content = export_excel()
            st.download_button(
                "Download file", data=content, file_name="survey_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Export failed: {e}")

st.success("Logged in.")

st.markdown("---")

# ------------------------------ UI: Create new question ------------------------------

st.header("Create new question")

c1, c2 = st.columns([3, 2])
with c1:
    new_text = st.text_input("Question text", key="new_text")
with c2:
    new_type = st.selectbox("Type", TYPE_CHOICES, index=0, key="new_type")

new_order = st.number_input("Order (integer)", value=999, step=1, key="new_order")

# NOTE block inputs (only for UI; not stored as answers)
note_img = note_cap = ""
note_w = 600

raw_opts = ""  # for single/multi

if new_type == "note":
    st.subheader("Note block (only UI — not stored as an answer)")
    note_img = st.text_input("Image URL (optional)", value="", key="new_note_img")
    note_cap = st.text_input("Caption (optional)", value="", key="new_note_cap")
    note_w   = st.number_input("Image width (px)", value=600, min_value=0, step=50, key="new_note_w")
elif new_type in ("single", "multi"):
    raw_opts = st.text_area(
        "Options (code:Label, comma separated)",
        placeholder="do:Dortmund Hbf, es:Essen Hbf, du:Düsseldorf Hbf",
        key="new_raw_opts"
    )

if st.button("Save question"):
    try:
        # 1) Build options by type
        new_options = []
        if new_type == "note":
            # one object describing image/caption/width
            w = int(note_w) if note_w and int(note_w) > 0 else None
            new_options = [{
                "image_url": (note_img or "").strip(),
                "caption":   (note_cap or "").strip(),
                "image_width": w
            }]
        elif new_type in ("single", "multi"):
            if raw_opts.strip():
                parts = [p.strip() for p in raw_opts.split(",") if p.strip()]
                for i, chunk in enumerate(parts):
                    if ":" in chunk:
                        code, label = chunk.split(":", 1)
                        new_options.append({
                            "code": code.strip(),
                            "label": label.strip(),
                            "oorder": i
                        })
        else:
            # text -> no options
            new_options = []

        payload = {
            "text": new_text,
            "qtype": new_type,
            "qorder": int(new_order),
            "options": new_options
        }
        res = create_question(payload)
        st.success(f"Saved. id={res.get('id')}")
        get_questions.clear()  # refresh cache
    except Exception as e:
        st.error(f"Save failed: {e}")

st.markdown("---")

# ------------------------------ UI: Existing questions ------------------------------

st.header("Existing questions")

try:
    qs = get_questions()
except Exception as e:
    st.error(f"Load questions failed: {e}")
    qs = []

if not qs:
    st.info("No questions.")
else:
    for q in qs:
        qid = q["id"]
        with st.expander(f"[{qid}] {q['text']}"):
            # -------- fields
            t = st.text_input("Text", value=q["text"], key=f"t_{qid}")

            curr_type = get_qtype(q)
            try:
                idx = TYPE_CHOICES.index(curr_type)
            except ValueError:
                idx = 0

            tp = st.selectbox("Type", TYPE_CHOICES, index=idx, key=f"type_{qid}")
            ordr = st.number_input("Order", value=q.get("order", 0), step=1, key=f"ord_{qid}")

            # dynamic inputs per type
            # for note
            note_img2 = note_cap2 = ""
            note_w2 = 0
            # for single/multi
            raw2 = ""

            if tp in ("single", "multi"):
                cur = ", ".join([f"{o.get('code','')}:{o.get('label','')}" for o in (q.get("options") or [])])
                raw2 = st.text_area("Options (code:Label, comma separated)", value=cur, key=f"opts_{qid}")

            elif tp == "note":
                meta = (q.get("options") or [{}])[0] if isinstance(q.get("options"), list) else {}
                note_img2 = st.text_input("Image URL (optional)", value=meta.get("image_url", ""), key=f"img_{qid}")
                note_cap2 = st.text_input("Caption (optional)", value=meta.get("caption", ""), key=f"cap_{qid}")
                try:
                    note_w_def = int(meta.get("image_width") or 0)
                except Exception:
                    note_w_def = 0
                note_w2 = st.number_input("Image width (px)", min_value=0, value=note_w_def, step=50, key=f"w_{qid}")

            # -------- buttons
            c_upd, c_del, c_sp = st.columns([1, 1, 6])

            with c_upd:
                if st.button("Update", key=f"upd_{qid}"):
                    try:
                        # build new options
                        newopts = []
                        if tp == "note":
                            w = int(note_w2) if note_w2 and int(note_w2) > 0 else None
                            newopts = [{
                                "image_url": (note_img2 or "").strip(),
                                "caption":   (note_cap2 or "").strip(),
                                "image_width": w
                            }]
                        elif tp in ("single", "multi"):
                            if raw2.strip():
                                parts = [p.strip() for p in raw2.split(",") if p.strip()]
                                for i, chunk in enumerate(parts):
                                    if ":" in chunk:
                                        code, label = chunk.split(":", 1)
                                        newopts.append({
                                            "code": code.strip(),
                                            "label": label.strip(),
                                            "oorder": i
                                        })
                        else:
                            newopts = []

                        payload = {
                            "text": t,
                            "qtype": tp,
                            "qorder": int(ordr),
                            "options": newopts
                        }
                        update_question(qid, payload)
                        st.success("Updated.")
                        get_questions.clear()
                    except Exception as e:
                        st.error(f"Update failed: {e}")

            with c_del:
                if st.button("Delete", key=f"del_{qid}"):
                    try:
                        delete_question(qid)
                        st.success("Deleted.")
                        get_questions.clear()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
