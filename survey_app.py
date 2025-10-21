# Form (styled via CSS on [data-testid="stForm"])
with st.form("survey_form"):
    for idx, q in enumerate(questions, start=1):
        qid   = q["id"]
        qtext = q.get("text", "")
        # بک‌اند گاهی qtype و گاهی type برمی‌گرداند؛ هر دو را پوشش بده
        qtype = q.get("qtype") or q.get("type") or "single"
        opts  = q.get("options", []) or []
        key_base = f"q_{qid}"

        # --- NOTE: فقط نمایش؛ بدون شماره و بدون پاسخ ---
        if qtype == "note":
            if qtext:
                st.markdown(f"**{qtext}**")

            # متای تصویر/کپشن/عرض از options[0]
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
            continue  # خیلی مهم: برو سؤال بعدی

        # --- هدر سؤال با شماره (برای سوال‌های غیر نوت) ---
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
            labels = [o.get("label", "") for o in opts]
            label_to_code = {o.get("label", ""): o.get("code", "") for o in opts}
            choice = st.radio(
                label="",
                options=labels if labels else ["(no options)"],
                key=key_base,
                horizontal=False,
                label_visibility="collapsed",
            )
            st.session_state.answers[qid] = label_to_code.get(choice, "")

        elif qtype == "multi":
            selected_codes = []
            for o in opts:  # ترتیب گزینه‌ها همان ترتیب بک‌اند
                code = o.get("code", "")
                label = o.get("label", "")
                chk = st.checkbox(label, key=f"{key_base}_{code}")
                if chk:
                    selected_codes.append(code)
            st.session_state[key_base] = selected_codes
            st.session_state.answers[qid] = selected_codes

        else:  # text
            txt = st.text_area(
                label="Your answer",
                key=f"{key_base}_text",
                height=110,
                label_visibility="collapsed",
            )
            st.session_state.answers[qid] = (txt or "").strip()

        # جداکننده بین سؤال‌ها
        st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

    # دکمه‌ها باید داخل همین فرم باشند
    col_left, col_right = st.columns([1, 1])
    with col_left:
        reset = st.form_submit_button("Reset", type="secondary")
    with col_right:
        submitted = st.form_submit_button("Submit", use_container_width=True)
