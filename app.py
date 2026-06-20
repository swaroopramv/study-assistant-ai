"""Study Assistant AI - Streamlit web UI.

Run with: streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from utils.rag_helper import (
    CHAT_MODEL,
    DATA_DIR,
    OLLAMA_BASE_URL,
    build_qa_chain,
    build_vectorstore,
    load_vectorstore,
    summarize_notes,
)

load_dotenv()

st.set_page_config(page_title="Study Assistant AI", page_icon="📚", layout="wide")


def ensure_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chain" not in st.session_state:
        st.session_state.chain = None


def init_chain(rebuild: bool = False):
    with st.spinner("Indexing your notes..."):
        vectorstore = build_vectorstore() if rebuild else load_vectorstore()
        st.session_state.chain = build_qa_chain(vectorstore)


ensure_state()

st.title("📚 Study Assistant AI")
st.caption("Ask questions about your notes and get instant, grounded answers.")

with st.sidebar:
    st.header("⚙️ Setup")

    st.markdown(f"**LLM:** `{CHAT_MODEL}` (Ollama)")
    st.markdown(f"**Ollama URL:** `{OLLAMA_BASE_URL}`")
    try:
        notes_display = DATA_DIR.relative_to(Path.cwd())
    except ValueError:
        notes_display = DATA_DIR.name
    st.markdown(f"**Notes folder:** `{notes_display}`")

    uploaded = st.file_uploader(
        "Add study material", type=["txt", "md", "pdf"], accept_multiple_files=True
    )
    if uploaded:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        for f in uploaded:
            (DATA_DIR / f.name).write_bytes(f.getbuffer())
        st.success(f"Saved {len(uploaded)} file(s). Click 'Rebuild index'.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Build / Load", use_container_width=True):
            init_chain(rebuild=False)
    with col2:
        if st.button("Rebuild index", use_container_width=True):
            init_chain(rebuild=True)

    if st.button("📝 Summarize notes", use_container_width=True):
        with st.spinner("Summarizing..."):
            try:
                st.session_state.summary = summarize_notes()
            except Exception as e:  # noqa: BLE001
                st.error(str(e))

if "summary" in st.session_state:
    with st.expander("📝 Notes Summary", expanded=True):
        st.markdown(st.session_state.summary)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question about your notes..."):
    if st.session_state.chain is None:
        try:
            init_chain(rebuild=False)
        except Exception as e:  # noqa: BLE001
            st.error(str(e))
            st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = st.session_state.chain.invoke(prompt)
            except Exception as e:  # noqa: BLE001
                answer = f"Error: {e}"
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
