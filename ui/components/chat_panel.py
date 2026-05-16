import asyncio

import streamlit as st

from ui.utils.api_client import query_nl2sql
from ui.utils.state import add_assistant_message, add_user_message


def render_chat():
    st.title("NL2SQL RAG — Hive Query Assistant")
    st.caption("Ask questions about your data in natural language and get HiveQL SQL.")

    # Display message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:
                if msg.get("reasoning") and st.session_state.show_reasoning:
                    with st.expander(" Reasoning process"):
                        st.markdown(msg["reasoning"])

                st.code(msg["sql"], language="sql")

                # Metadata
                meta_parts = []
                if msg.get("tables"):
                    meta_parts.append(f"Tables: {', '.join(msg['tables'])}")
                if msg.get("elapsed"):
                    meta_parts.append(f"Time: {msg['elapsed']:.0f}ms")
                if msg.get("warnings"):
                    for w in msg["warnings"]:
                        st.warning(f" {w}")

                if meta_parts:
                    st.caption(" | ".join(meta_parts))

    # Chat input
    if prompt := st.chat_input("Ask a question about your Hive data..."):
        add_user_message(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = asyncio.run(query_nl2sql(
                        question=prompt,
                        top_k=st.session_state.top_k,
                        temperature=st.session_state.temperature,
                        include_reasoning=st.session_state.show_reasoning,
                        few_shot=st.session_state.few_shot,
                    ))
                except Exception as e:
                    st.error(f"Error: {e}")
                    return

            sql = response.get("sql", "-- Error generating SQL")
            reasoning = response.get("reasoning")
            tables = response.get("retrieved_tables", [])
            warnings = response.get("warnings", [])
            elapsed = response.get("execution_time_ms", 0)

            add_assistant_message(
                content="Generated SQL:",
                sql=sql,
                reasoning=reasoning,
                tables=tables,
                warnings=warnings,
                elapsed=elapsed,
            )

            # Display current response
            if reasoning and st.session_state.show_reasoning:
                with st.expander(" Reasoning process"):
                    st.markdown(reasoning)

            st.code(sql, language="sql")

            if warnings:
                for w in warnings:
                    st.warning(f" {w}")

            meta_parts = []
            if tables:
                meta_parts.append(f"Tables: {', '.join(tables)}")
            if elapsed:
                meta_parts.append(f"Time: {elapsed:.0f}ms")
            if meta_parts:
                st.caption(" | ".join(meta_parts))
