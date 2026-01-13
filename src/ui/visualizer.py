import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile


class StreamlitVisualizer:
    def __init__(self):
        self.colors = [
            "#241e4e",
            "#8fa998",
            "#CE6C47",
            "#FFD046",
            "#EADAA2",
            "#8fa998",
            "#BB8FCE",
            "#85C1E9",
        ]

    def render_graph(
        self, G: nx.DiGraph, activity_mapping: dict, subprocess_names: dict
    ):
        """
        Generates and displays the interactive PyVis graph.
        """
        net = Network(
            height="600px",
            width="100%",
            bgcolor="#ffffff",
            font_color="black",
            directed=True,
        )

        for node in G.nodes():
            sub_id = activity_mapping.get(node, 0)
            color = self.colors[sub_id % len(self.colors)]
            group_name = subprocess_names.get(sub_id, "Unknown")

            net.add_node(
                node,
                label=node,
                title=f"Activity: {node}\nPhase: {group_name}",
                color=color,
                size=25,
                shape="dot",
            )

        for src, tgt, data in G.edges(data=True):
            width = 1 + (data.get("weight", 1) / 50)  # simple scaling
            width = min(width, 5)

            net.add_edge(
                src,
                tgt,
                value=data.get("weight", 1),
                title=f"Frequency: {data.get('weight', 1)}",
                width=width,
                arrowStrikethrough=False,
            )

        net.set_options("""
        var options = {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -3500,
              "centralGravity": 0.3,
              "springLength": 180,
              "springConstant": 0.04,
              "damping": 0.09,
              "avoidOverlap": 0.2
            },
            "minVelocity": 0.75,
            "timestep": 0.5
          }
        }
        """)

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                net.save_graph(tmp.name)
                with open(tmp.name, "r", encoding="utf-8") as f:
                    html_data = f.read()

            st.components.v1.html(html_data, height=610)
        except Exception as e:
            st.error(f"Graph Rendering Error: {e}")

    def render_subprocess_details(self, subprocess_map: dict, subprocess_names: dict):
        """
        Renders the cards/expanders showing which activities are in which subprocess.
        """
        st.subheader("Subprocess Details")

        num_items = len(subprocess_map)
        if num_items == 1:
            cols = st.columns(1)
        else:
            cols = st.columns(3)

        for idx, (sub_id, activities) in enumerate(subprocess_map.items()):
            col = cols[idx % 3] if num_items > 1 else cols[0]
            with col:
                name = subprocess_names.get(sub_id, f"Group {sub_id}")
                with st.container(border=True):
                    st.markdown(f"**{name}**")
                    st.caption(f"{len(activities)} activities")
                    st.write(", ".join(activities))
