from inndxd_agents.graph import build_research_graph


def test_graph_builds_without_error():
    graph = build_research_graph()
    assert graph is not None
    assert hasattr(graph, "ainvoke")
