"""Research graph builder with conditional routing, quality gates, and retry limits."""

from langgraph.graph import END, START, StateGraph

from inndxd_agents.nodes.collector import collector_node
from inndxd_agents.nodes.human_approval import human_approval_node
from inndxd_agents.nodes.plan_validator import plan_validator_node
from inndxd_agents.nodes.planner import planner_node
from inndxd_agents.nodes.quality import evaluate_collected_data, evaluate_structured_items
from inndxd_agents.nodes.structurer import structurer_node
from inndxd_agents.state import ResearchState

MAX_COLLECTOR_RETRIES = 3
MAX_STRUCTURER_RETRIES = 2
MAX_PLANNER_RETRIES = 2


def should_proceed_after_validation(state: ResearchState) -> str:
    errors = state.get("errors", [])
    has_plan = bool(state.get("plan"))
    retries = state.get("planner_retries", 0)
    if not has_plan or (errors and retries < MAX_PLANNER_RETRIES):
        return "planner"
    return "collector"


def should_proceed_after_collection(state: ResearchState) -> str:
    collected = state.get("collected_data", [])
    retries = state.get("collector_retries", 0)
    if not evaluate_collected_data(collected) and retries < MAX_COLLECTOR_RETRIES:
        return "collector"
    return "structurer"


def should_retry_structure(state: ResearchState) -> str:
    structured = state.get("structured_items", [])
    retries = state.get("structurer_retries", 0)
    if not evaluate_structured_items(structured) and retries < MAX_STRUCTURER_RETRIES:
        return "structurer"
    return END


def build_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_node)
    graph.add_node("plan_validator", plan_validator_node)
    graph.add_node("collector", collector_node)
    graph.add_node("structurer", structurer_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "plan_validator")

    graph.add_conditional_edges(
        "plan_validator",
        should_proceed_after_validation,
        {
            "collector": "collector",
            "planner": "planner",
        },
    )

    graph.add_conditional_edges(
        "collector",
        should_proceed_after_collection,
        {
            "structurer": "structurer",
            "collector": "collector",
        },
    )

    graph.add_conditional_edges(
        "structurer",
        should_retry_structure,
        {
            "structurer": "structurer",
            END: END,
        },
    )

    return graph.compile()


def build_research_graph_with_approval():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_node)
    graph.add_node("plan_validator", plan_validator_node)
    graph.add_node("collector", collector_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("structurer", structurer_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "plan_validator")

    graph.add_conditional_edges(
        "plan_validator",
        should_proceed_after_validation,
        {"collector": "collector", "planner": "planner"},
    )

    graph.add_conditional_edges(
        "collector",
        should_proceed_after_collection,
        {"human_approval": "human_approval", "collector": "collector"},
    )

    graph.add_edge("human_approval", "structurer")

    graph.add_conditional_edges(
        "structurer",
        should_retry_structure,
        {"structurer": "structurer", END: END},
    )

    return graph.compile(interrupt_before=["human_approval"])


def serialize_state(state: ResearchState) -> dict:
    return {
        "brief_id": state.get("brief_id"),
        "tenant_id": state.get("tenant_id"),
        "project_id": state.get("project_id"),
        "natural_language": state.get("natural_language"),
        "plan": state.get("plan"),
        "collected_data": state.get("collected_data", []),
        "structured_items": state.get("structured_items", []),
        "errors": state.get("errors", []),
        "collector_retries": state.get("collector_retries", 0),
        "structurer_retries": state.get("structurer_retries", 0),
        "planner_retries": state.get("planner_retries", 0),
    }
