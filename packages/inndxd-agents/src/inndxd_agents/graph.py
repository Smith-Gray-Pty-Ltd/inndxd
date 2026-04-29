# packages/inndxd-agents/src/inndxd_agents/graph.py

from langgraph.graph import END, START, StateGraph

from inndxd_agents.nodes.collector import collector_node
from inndxd_agents.nodes.planner import planner_node
from inndxd_agents.nodes.structurer import structurer_node
from inndxd_agents.state import ResearchState


def build_research_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("planner", planner_node)
    graph.add_node("collector", collector_node)
    graph.add_node("structurer", structurer_node)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "collector")
    graph.add_edge("collector", "structurer")
    graph.add_edge("structurer", END)
    return graph.compile()
