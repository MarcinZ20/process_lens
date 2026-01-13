import streamlit as st
import pandas as pd
import sys
import os
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from miner.process_miner import ProcessMiner
from llm.llm_client import LlmClient
from ui.visualizer import StreamlitVisualizer

st.set_page_config(page_title="ProcessLens AI", layout="wide")


def main():
    st.sidebar.title("Subprocess project")

    env_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    api_key = st.sidebar.text_input("Gemini API Key", value=env_key, type="password")
    uploaded_file = st.sidebar.file_uploader("Upload CSV Log", type=["csv"])

    st.sidebar.subheader("Settings")
    granularity = st.sidebar.slider("Decomposition Granularity", 0.1, 3.0, 1.0, 0.1)
    enable_ai = st.sidebar.checkbox("Enable AI Naming", value=True)

    st.title("Process Decomposition")

    if not uploaded_file:
        st.info("Please upload a CSV file to begin.")
        keys_to_clear = ["raw_df", "nx_graph", "subprocess_map", "analysis_done"]
        for k in keys_to_clear:
            if k in st.session_state:
                del st.session_state[k]
        return

    file_key = f"file_{uploaded_file.name}_{uploaded_file.size}"

    if (
        "current_file_key" not in st.session_state
        or st.session_state.current_file_key != file_key
    ):
        uploaded_file.seek(0)
        st.session_state.raw_df = pd.read_csv(uploaded_file)
        st.session_state.current_file_key = file_key
        for key in ["nx_graph", "subprocess_map", "analysis_done"]:
            if key in st.session_state:
                del st.session_state[key]
        for key in ["col_case", "col_act", "col_time"]:
            if key in st.session_state:
                del st.session_state[key]

    df = st.session_state.raw_df
    all_columns = df.columns.tolist()

    st.subheader("1. Data Configuration")

    if "col_case" not in st.session_state:
        st.session_state.col_case = all_columns[0]
    if "col_act" not in st.session_state:
        st.session_state.col_act = (
            all_columns[1] if len(all_columns) > 1 else all_columns[0]
        )
    if "col_time" not in st.session_state:
        st.session_state.col_time = (
            all_columns[2] if len(all_columns) > 2 else all_columns[0]
        )

    def auto_detect_callback():
        curr_df = st.session_state.raw_df
        suggestions = ProcessMiner.suggest_columns(curr_df)
        st.session_state.col_case = suggestions["case_id"]
        st.session_state.col_act = suggestions["activity"]
        st.session_state.col_time = suggestions["timestamp"]
        st.toast("Columns Auto-Detected!", icon="✅")

    col1, col2, col3, col4 = st.columns([1, 1, 1, 0.5])
    with col4:
        st.write("")
        st.write("")
        st.button("Auto Detect", on_click=auto_detect_callback)
    with col1:
        case_col = st.selectbox("Case ID", all_columns, key="col_case")
    with col2:
        act_col = st.selectbox("Activity", all_columns, key="col_act")
    with col3:
        time_col = st.selectbox("Timestamp", all_columns, key="col_time")

    st.markdown("---")

    def run_analysis():
        st.session_state.analysis_done = True
        if "nx_graph" in st.session_state:
            del st.session_state.nx_graph
        if "subprocess_map" in st.session_state:
            del st.session_state.subprocess_map
        if "subprocess_names" in st.session_state:
            del st.session_state.subprocess_names

    if st.button("Analyze Process Model", type="primary", on_click=run_analysis):
        pass

    if st.session_state.get("analysis_done", False):
        try:
            if "nx_graph" not in st.session_state:
                miner = ProcessMiner(df.copy())
                llm = LlmClient(api_key)

                with st.spinner("Mining & Decomposing..."):
                    miner.prepare_data(case_col, act_col, time_col)
                    nx_graph, subprocess_map, activity_mapping = (
                        miner.mine_and_decompose(resolution=granularity)
                    )

                    st.session_state.nx_graph = nx_graph
                    st.session_state.subprocess_map = subprocess_map
                    st.session_state.activity_mapping = activity_mapping

                    subprocess_names = {}
                    if enable_ai and llm.is_active:
                        progress_bar = st.progress(0)
                        status = st.empty()
                        total = len(subprocess_map)
                        for i, (sub_id, activities) in enumerate(
                            subprocess_map.items()
                        ):
                            status.text(f"Naming Group {i + 1}/{total}...")
                            name = llm.get_subprocess_name(activities, sub_id)
                            subprocess_names[sub_id] = name
                            progress_bar.progress((i + 1) / total)
                        progress_bar.empty()
                        status.empty()
                    else:
                        for sub_id in subprocess_map.keys():
                            subprocess_names[sub_id] = f"Subprocess {sub_id}"

                    st.session_state.subprocess_names = subprocess_names

            nx_graph = st.session_state.nx_graph
            subprocess_map = st.session_state.subprocess_map
            activity_mapping = st.session_state.activity_mapping
            subprocess_names = st.session_state.subprocess_names
            visualizer = StreamlitVisualizer()

            st.subheader("2. Process Visualization")

            view_options = ["Show Entire Process"] + [
                str(name) for name in subprocess_names.values()
            ]
            selected_view = st.selectbox("Select View Focus:", view_options)

            graph_to_render = nx_graph
            map_to_render = subprocess_map

            if selected_view != "Show Entire Process":
                selected_id = next(
                    (
                        id
                        for id, name in subprocess_names.items()
                        if str(name) == selected_view
                    ),
                    None,
                )

                if selected_id is not None:
                    target_nodes = subprocess_map.get(selected_id, [])
                    if target_nodes:
                        graph_to_render = nx_graph.subgraph(target_nodes)
                        map_to_render = {selected_id: target_nodes}
                else:
                    st.warning(
                        "Could not locate the selected subprocess. Showing full graph."
                    )

            col_viz, col_stats = st.columns([3, 1])

            with col_viz:
                visualizer.render_graph(
                    graph_to_render, activity_mapping, subprocess_names
                )

            with col_stats:
                st.info(
                    f"**Nodes:** {len(graph_to_render.nodes)}\n\n**Edges:** {len(graph_to_render.edges)}"
                )
                if selected_view != "Show Entire Process":
                    st.caption(
                        "You are viewing an isolated subprocess. Select 'Show Entire Process' to see the full flow."
                    )

            visualizer.render_subprocess_details(map_to_render, subprocess_names)

        except Exception as e:
            st.error(f"Analysis Error: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
