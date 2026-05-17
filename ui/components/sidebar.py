import asyncio

import streamlit as st

from ui.utils.api_client import get_schema, health_check, reindex


def render_sidebar():
    with st.sidebar:
        st.header(" 配置")

        st.session_state.top_k = st.slider(
            "检索数量 (Top-K)",
            min_value=1, max_value=30,
            value=st.session_state.top_k,
            help="检索的 schema 片段数量",
        )

        st.session_state.temperature = st.slider(
            "温度参数",
            min_value=0.0, max_value=1.0,
            value=st.session_state.temperature,
            step=0.05,
            help="LLM 生成温度",
        )

        st.session_state.show_reasoning = st.checkbox(
            "显示推理过程",
            value=st.session_state.show_reasoning,
            help="显示模型的思维链",
        )

        st.session_state.few_shot = st.checkbox(
            "启用 Few-Shot 示例",
            value=st.session_state.few_shot,
            help="在提示词中包含示例",
        )

        st.divider()

        st.header(" 数据表")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(" 刷新数据表"):
                with st.spinner("加载中..."):
                    try:
                        tables = asyncio.run(get_schema())
                        st.session_state.tables = tables
                    except Exception as e:
                        st.error(f"加载失败: {e}")

        with col2:
            if st.button(" 重新索引"):
                with st.spinner("索引重建中..."):
                    try:
                        result = asyncio.run(reindex())
                        st.success(f"{result['report']['num_tables']} 个表已索引")
                    except Exception as e:
                        st.error(f"索引失败: {e}")

        # Show loaded tables
        if "tables" in st.session_state and st.session_state.tables:
            st.write(f"**已加载 {len(st.session_state.tables)} 个表**")
            for t in st.session_state.tables[:50]:
                with st.expander(f" {t['name']} ({t.get('num_fields', 0)} 个字段)"):
                    st.caption(f"子系统: {t.get('subs_code', 'N/A')}")
        else:
            st.caption("暂无表信息，请点击「刷新数据表」")

        st.divider()

        # Health indicator
        if st.button(" 健康检查"):
            try:
                h = asyncio.run(health_check())
                if h["status"] == "ok":
                    st.success(" 所有系统正常")
                else:
                    st.warning(" 服务降级")
                st.json(h)
            except Exception as e:
                st.error(f"无法连接 API: {e}")
