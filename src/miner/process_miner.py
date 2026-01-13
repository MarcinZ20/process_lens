import pandas as pd
import pm4py
import networkx as nx
from typing import Tuple, Dict
import re

class ProcessMiner:
    def __init__(self, dataframe: pd.DataFrame):
        self.log = dataframe.copy()
        self.G = None

    @staticmethod
    def suggest_columns(df: pd.DataFrame) -> Dict[str, str]:
        columns = df.columns.tolist()
        keywords = {
            'timestamp': ['start', 'begin', 'create', 'date', 'time', 'timestamp'],
            'activity': ['activity', 'task', 'action', 'state', 'status', 'event', 'operation'],
            'case_id': ['case', 'id', 'label', 'instance', 'identifier', 'ticket', 'trace']
        }
        suggestions = {}
        for target, patterns in keywords.items():
            best_col = None
            best_score = -1
            for col in columns:
                score = 0
                col_lower = col.lower()
                if col_lower == target: score += 10
                for pattern in patterns:
                    if pattern in col_lower: score += 3 + (1 / len(col))
                if score > best_score and score > 0:
                    best_score = score
                    best_col = col
            suggestions[target] = best_col if best_col else columns[0]
        return suggestions

    def prepare_data(self, case_col: str, activity_col: str, timestamp_col: str):
        """
        Renames and formats the dataframe based on selected columns.
        Uses format='mixed' to handle inconsistent date formats robustly.
        """
        self.log[timestamp_col] = pd.to_datetime(
            self.log[timestamp_col],
            format='mixed',
            dayfirst=True,
            errors='coerce'
        )

        if self.log[timestamp_col].isna().any():
            print(f"Warning: Dropped {self.log[timestamp_col].isna().sum()} rows with invalid dates.")
            self.log = self.log.dropna(subset=[timestamp_col])

        self.log = pm4py.format_dataframe(
            self.log,
            case_id=case_col,
            activity_key=activity_col,
            timestamp_key=timestamp_col
        )

        self.log = self.log.rename(columns={
            case_col: 'case_id',
            activity_col: 'activity',
            timestamp_col: 'start_date'
        })

    def mine_and_decompose(self, resolution: float = 1.0) -> Tuple[nx.DiGraph, Dict[int, list], Dict[str, int]]:
        dfg, _, _ = pm4py.discover_dfg(self.log)
        self.G = nx.DiGraph()
        for (src, tgt), weight in dfg.items():
            self.G.add_edge(src, tgt, weight=weight)

        undirected_G = self.G.to_undirected()

        if len(undirected_G.nodes) == 0:
            return self.G, {}, {}

        communities = nx.community.greedy_modularity_communities(
            undirected_G,
            weight='weight',
            resolution=resolution
        )

        subprocess_map = {}
        activity_mapping = {}

        for idx, community in enumerate(communities):
            sorted_activities = sorted(list(community))
            subprocess_map[idx] = sorted_activities
            for act in sorted_activities:
                activity_mapping[act] = idx

        return self.G, subprocess_map, activity_mapping
