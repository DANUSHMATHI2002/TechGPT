import os
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit_option_menu import option_menu

load_dotenv()

st.set_page_config(page_title="TechGPT · Chat with your data", page_icon="🤖", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
.block-container{padding-top:2rem;max-width:1300px}
.hero{background:linear-gradient(120deg,#4f46e5 0%,#7c3aed 55%,#06b6d4 100%);
      padding:38px 40px;border-radius:20px;color:#fff;margin-bottom:22px}
.hero h1{margin:0 0 6px;font-size:2.2rem;color:#fff}
.hero p{margin:0;opacity:.92;font-size:1.05rem}
.feat{border:1px solid rgba(128,128,128,.25);border-radius:16px;padding:20px;height:100%}
.feat h4{margin:6px 0}.feat p{opacity:.75;font-size:.92rem;margin:0}
.pill{display:inline-block;padding:2px 10px;border-radius:99px;font-size:.78rem;
      background:rgba(124,58,237,.15);color:#7c3aed;font-weight:600}
#MainMenu,footer,[data-testid="stToolbar"]{visibility:hidden}
</style>
""", unsafe_allow_html=True)

# ---------- State ----------
st.session_state.setdefault("df", None)
st.session_state.setdefault("filename", None)
st.session_state.setdefault("messages", [])


# ---------- Helpers ----------
@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes) -> pd.DataFrame:
    import io
    return pd.read_csv(io.BytesIO(file_bytes))


def ask_llm(df: pd.DataFrame, prompt: str, api_key: str):
    from pandasai.llm.openai import OpenAI
    llm = OpenAI(api_token=api_key)
    try:  # newer pandasai
        from pandasai import SmartDataframe
        return SmartDataframe(df, config={"llm": llm}).chat(prompt)
    except ImportError:  # older pandasai
        from pandasai import PandasAI
        return PandasAI(llm).run(df, prompt=prompt)


def render_result(res):
    if isinstance(res, pd.DataFrame):
        st.dataframe(res, use_container_width=True)
    elif isinstance(res, str) and res.lower().endswith((".png", ".jpg", ".jpeg")) and os.path.exists(res):
        st.image(res)
    else:
        st.markdown(str(res))


def profile(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Column": df.columns,
        "Type": df.dtypes.astype(str).values,
        "Non-null": df.notna().sum().values,
        "Unique": df.nunique().values,
        "Missing %": (df.isna().mean() * 100).round(1).values,
    })


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 🤖 TechGPT")
    selected = option_menu(
        None, ["Home", "TechGPT", "Help"],
        icons=["house", "chat-dots", "question-circle"], default_index=0,
        styles={"nav-link-selected": {"background-color": "#7c3aed"}},
    )
    st.divider()
    api_key = st.text_input("OpenAI API key", type="password",
                            value=os.getenv("OPENAI_API_KEY", ""),
                            help="Stored only in this session. You can also set OPENAI_API_KEY in a .env file.")
    if st.session_state.df is not None:
        st.success(f"📄 {st.session_state.filename}\n\n{len(st.session_state.df):,} rows × {st.session_state.df.shape[1]} cols")
    else:
        st.info("No dataset loaded")
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------- Home ----------
if selected == "Home":
    st.markdown("""<div class="hero"><span class="pill" style="background:rgba(255,255,255,.2);color:#fff">AI Data Assistant</span>
    <h1>Talk to your data. Get answers instantly.</h1>
    <p>Upload a CSV, explore it visually, and ask questions in plain English.</p></div>""", unsafe_allow_html=True)
    c = st.columns(3)
    feats = [("📤", "Upload", "Drop in any CSV and see it instantly with a full data profile."),
             ("📊", "Explore", "Check missing values, types, distributions and build quick charts."),
             ("💬", "Chat", "Ask questions like “top 5 products by revenue” and get tables or charts.")]
    for col, (ic, t, d) in zip(c, feats):
        col.markdown(f'<div class="feat"><div style="font-size:1.8rem">{ic}</div><h4>{t}</h4><p>{d}</p></div>',
                     unsafe_allow_html=True)
    st.markdown("&nbsp;")
    st.markdown("**Get started:** open **TechGPT** in the sidebar, upload a file and start asking.")

# ---------- TechGPT ----------
elif selected == "TechGPT":
    st.title("TechGPT Workspace")
    up = st.file_uploader("Upload your CSV file", type=["csv"])
    if up is not None:
        try:
            is_new = st.session_state.filename != up.name
            st.session_state.df = load_csv(up.getvalue())
            st.session_state.filename = up.name
            if is_new:
                st.rerun()  # refresh sidebar status
        except Exception as e:
            st.error(f"Could not read the file: {e}")

    df = st.session_state.df
    if df is None:
        st.info("⬆️ Upload a CSV to begin.")
        st.stop()

    k = st.columns(4)
    k[0].metric("Rows", f"{len(df):,}")
    k[1].metric("Columns", df.shape[1])
    k[2].metric("Missing cells", f"{df.isna().mean().mean() * 100:.1f}%")
    k[3].metric("Duplicate rows", f"{df.duplicated().sum():,}")

    tab_prev, tab_prof, tab_viz, tab_chat = st.tabs(["📄 Preview", "🧪 Data profile", "📊 Visual explorer", "💬 Chat"])

    with tab_prev:
        st.dataframe(df, use_container_width=True, height=420)
        st.download_button("⬇️ Download as CSV", df.to_csv(index=False), "data.csv", "text/csv")

    with tab_prof:
        st.dataframe(profile(df), use_container_width=True, hide_index=True)
        num = df.select_dtypes("number")
        if not num.empty:
            st.markdown("**Numeric summary**")
            st.dataframe(num.describe().T.round(2), use_container_width=True)

    with tab_viz:
        num_cols = df.select_dtypes("number").columns.tolist()
        all_cols = df.columns.tolist()
        c1, c2, c3 = st.columns(3)
        kind = c1.selectbox("Chart type", ["Bar (mean)", "Line", "Scatter", "Histogram"])
        if kind == "Histogram":
            col = c2.selectbox("Column", num_cols) if num_cols else None
            if col:
                counts, edges = np.histogram(df[col].dropna(), bins=20)
                st.bar_chart(pd.DataFrame({"count": counts}, index=edges[:-1].round(2)))
            else:
                st.warning("No numeric columns available.")
        elif not num_cols:
            st.warning("No numeric columns available.")
        else:
            cat_cols = [c for c in all_cols if df[c].nunique() <= 20]
            x = c2.selectbox("X axis", all_cols, index=all_cols.index(cat_cols[0]) if cat_cols else 0)
            y = c3.selectbox("Y axis", num_cols, index=num_cols.index("revenue") if "revenue" in num_cols else 0)
            if kind == "Bar (mean)":
                st.bar_chart(df.groupby(x)[y].mean().head(40))
            elif kind == "Line":
                st.line_chart(df.set_index(x)[y])
            else:
                st.scatter_chart(df, x=x, y=y)

    with tab_chat:
        suggestions = ["Summarise this dataset", "Which columns have missing values?",
                       "Show the top 5 rows by the largest numeric column"]
        sc = st.columns(len(suggestions))
        picked = None
        for col, s in zip(sc, suggestions):
            if col.button(s, use_container_width=True):
                picked = s

        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                if m["role"] == "assistant":
                    render_result(m["content"])
                else:
                    st.markdown(m["content"])

        prompt = st.chat_input("Ask something about your data…") or picked
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                if not api_key:
                    res = "⚠️ Please add your OpenAI API key in the sidebar."
                else:
                    with st.spinner("Analysing…"):
                        try:
                            res = ask_llm(df, prompt, api_key)
                        except Exception as e:
                            res = f"❌ Something went wrong: {e}"
                render_result(res)
            st.session_state.messages.append({"role": "assistant", "content": res})

        if st.session_state.messages:
            log = "\n\n".join(f"[{m['role'].upper()}] {m['content']}" for m in st.session_state.messages)
            st.download_button("⬇️ Export chat", log, f"chat_{datetime.now():%Y%m%d_%H%M}.txt")

# ---------- Help ----------
else:
    st.title("Help & FAQ")
    with st.expander("How do I use TechGPT?", expanded=True):
        st.write("Go to **TechGPT**, upload a CSV, then open the **Chat** tab and ask questions in plain English.")
    with st.expander("What can I ask?"):
        st.write("Summaries, filters, aggregations, rankings and charts, e.g. *“Average sales by region”* or *“Plot revenue over time”*.")
    with st.expander("Where do I put my API key?"):
        st.write("Paste it in the sidebar, or set `OPENAI_API_KEY` in a `.env` file. Never hard-code it or commit it to GitHub.")
    with st.expander("Is my data private?"):
        st.write("The CSV stays in your session. Column names and sample rows may be sent to OpenAI to answer your questions.")
