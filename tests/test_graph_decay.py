import pytest
import time
import sys
import os
from datetime import datetime, timedelta

# Bypassing circular import in __init__
from memory.graph_rag import GraphRAG

def test_temporal_decay():
    graph_rag = GraphRAG()

    # Manually add entities and relationship to ensure they exist
    graph_rag.graph.add_node("Alice", type="person")
    graph_rag.graph.add_node("Google", type="project")
    graph_rag.graph.add_edge("Alice", "Google", weight=1.0, last_seen=datetime.now().isoformat())

    # Verify edge exists with weight 1.0
    edge_data = graph_rag.graph["Alice"]["Google"]
    assert edge_data["weight"] == 1.0
    original_timestamp = edge_data["last_seen"]

    # Manually set the timestamp to 30 days ago to trigger decay
    old_time = (datetime.now() - timedelta(days=30)).isoformat()
    graph_rag.graph["Alice"]["Google"]["last_seen"] = old_time

    # Adding new data triggers decay
    graph_rag.add_to_graph("Bob works at Microsoft")

    # Verify Alice->Google edge has decayed (half-life is 30 days, so weight should be ~0.5)
    decayed_weight = graph_rag.graph["Alice"]["Google"]["weight"]
    assert decayed_weight < 1.0
    assert 0.4 <= decayed_weight <= 0.6
