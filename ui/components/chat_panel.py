import asyncio

import streamlit as st

from ui.utils.api_client import query_nl2sql
from ui.utils.state import add_assistant_message, add_user_message


def render_chat():
    st.title("NL2SQL — Hive 查询助手")
    st.caption("用自然语言提问，自动生成 HiveSQL 查询语句")

    # Display message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:
                if msg.get("reasoning") and st.session_state.show_reasoning:
                    with st.expander(" 推理过程"):
                        st.markdown(msg["reasoning"])

                st.code(msg["sql"], language="sql")

                # Metadata
                meta_parts = []
                if msg.get("tables"):
                    meta_parts.append(f"涉及表: {', '.join(msg['tables'])}")
                if msg.get("applied_rules"):
                    rule_descs = [f"{r['table']}({r['condition']})" for r in msg["applied_rules"]]
                    meta_parts.append(f"已应用规则: {', '.join(rule_descs)}")
                if msg.get("elapsed"):
                    meta_parts.append(f"耗时: {msg['elapsed']:.0f}ms")
                if msg.get("warnings"):
                    for w in msg["warnings"]:
                        st.warning(f" {w}")

                if meta_parts:
                    st.caption(" | ".join(meta_parts))

    # Chat input
    if prompt := st.chat_input("请输入您关于 Hive 数据的查询问题..."):
        add_user_message(prompt)

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    response = asyncio.run(query_nl2sql(
                        question=prompt,
                        top_k=st.session_state.top_k,
                        temperature=st.session_state.temperature,
                        include_reasoning=st.session_state.show_reasoning,
                        few_shot=st.session_state.few_shot,
                    ))
                except Exception as e:
                    st.error(f"请求失败: {e}")
                    return

            sql = response.get("sql", "-- SQL 生成失败")
            reasoning = response.get("reasoning")
            tables = response.get("retrieved_tables", [])
            warnings = response.get("warnings", [])
            elapsed = response.get("execution_time_ms", 0)
            applied_rules = response.get("applied_rules", [])

            add_assistant_message(
                content="生成的 SQL:",
                sql=sql,
                reasoning=reasoning,
                tables=tables,
                warnings=warnings,
                elapsed=elapsed,
                applied_rules=applied_rules,
            )

            # Display current response
            if reasoning and st.session_state.show_reasoning:
                with st.expander(" 推理过程"):
                    st.markdown(reasoning)

            st.code(sql, language="sql")

            if warnings:
                for w in warnings:
                    st.warning(f" {w}")

            meta_parts = []
            if tables:
                meta_parts.append(f"涉及表: {', '.join(tables)}")
            if applied_rules:
                rule_descs = [f"{r['table']}({r['condition']})" for r in applied_rules]
                meta_parts.append(f"已应用规则: {', '.join(rule_descs)}")
            if elapsed:
                meta_parts.append(f"耗时: {elapsed:.0f}ms")
            if meta_parts:
                st.caption(" | ".join(meta_parts))
