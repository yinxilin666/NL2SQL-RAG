import asyncio

import streamlit as st

from ui.utils.api_client import get_schema, health_check, reindex


def render_sidebar():
    with st.sidebar:
        st.header(" Configuration")

        st.session_state.top_k = st.slider(
            "Top-K chunks",
            min_value=1, max_value=30,
            value=st.session_state.top_k,
            help="Number of schema chunks to retrieve",
        )

        st.session_state.temperature = st.slider(
            "Temperature",
            min_value=0.0, max_value=1.0,
            value=st.session_state.temperature,
            step=0.05,
            help="LLM generation temperature",
        )

        st.session_state.show_reasoning = st.checkbox(
            "Show reasoning process",
            value=st.session_state.show_reasoning,
            help="Display the model's chain-of-thought",
        )

        st.session_state.few_shot = st.checkbox(
            "Use few-shot examples",
            value=st.session_state.few_shot,
            help="Include examples in prompt",
        )

        st.divider()

        st.header(" Schema")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(" Refresh Schema"):
                with st.spinner("Loading..."):
                    try:
                        tables = asyncio.run(get_schema())
                        st.session_state.tables = tables
                    except Exception as e:
                        st.error(f"Failed: {e}")

        with col2:
            if st.button(" Re-index"):
                with st.spinner("Re-indexing..."):
                    try:
                        result = asyncio.run(reindex())
                        st.success(f"{result['report']['num_tables']} tables indexed")
                    except Exception as e:
                        st.error(f"Failed: {e}")

        # Show loaded tables
        if "tables" in st.session_state and st.session_state.tables:
            st.write(f"**{len(st.session_state.tables)} tables loaded**")
            for t in st.session_state.tables[:50]:
                with st.expander(f" {t['name']} ({t.get('num_fields', 0)} fields)"):
                    st.caption(f"Subsystem: {t.get('subs_code', 'N/A')}")
        else:
            st.caption("No tables loaded. Click 'Refresh Schema'")

        st.divider()

        # Health indicator
        if st.button(" Health Check"):
            try:
                h = asyncio.run(health_check())
                if h["status"] == "ok":
                    st.success(" All systems OK")
                else:
                    st.warning(" Degraded")
                st.json(h)
            except Exception as e:
                st.error(f"Cannot reach API: {e}")
