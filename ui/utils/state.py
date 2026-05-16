import streamlit as st


DEFAULTS = {
    "model": "deepseek-r1:8b",
    "top_k": 8,
    "temperature": 0.1,
    "show_reasoning": False,
    "few_shot": True,
}


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def add_user_message(content: str):
    st.session_state.messages.append({
        "role": "user",
        "content": content,
    })


def add_assistant_message(content: str, sql: str, reasoning: str | None,
                           tables: list[str], warnings: list[str], elapsed: float):
    st.session_state.messages.append({
        "role": "assistant",
        "content": content,
        "sql": sql,
        "reasoning": reasoning,
        "tables": tables,
        "warnings": warnings,
        "elapsed": elapsed,
    })
