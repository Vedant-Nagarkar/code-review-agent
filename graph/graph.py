from langgraph.graph import StateGraph, END
from graph.state import CodeReviewState
from agents.planner import planner_node
from agents.security import security_node
from agents.performance import performance_node
from agents.style import style_node
from agents.test_coverage import test_coverage_node
from agents.critic import critic_node, should_retry
from agents.synthesizer import synthesizer_node


def build_graph() -> StateGraph:
    graph = StateGraph(CodeReviewState)

    # Add all nodes
    graph.add_node("planner", planner_node)
    graph.add_node("security", security_node)
    graph.add_node("performance", performance_node)
    graph.add_node("style", style_node)
    graph.add_node("test_coverage", test_coverage_node)
    graph.add_node("critic", critic_node)
    graph.add_node("synthesizer", synthesizer_node)

    # Entry point
    graph.set_entry_point("planner")

    # Planner fans out to all specialist agents in parallel
    graph.add_edge("planner", "security")
    graph.add_edge("planner", "performance")
    graph.add_edge("planner", "style")
    graph.add_edge("planner", "test_coverage")

    # All specialists feed into critic
    graph.add_edge("security", "critic")
    graph.add_edge("performance", "critic")
    graph.add_edge("style", "critic")
    graph.add_edge("test_coverage", "critic")

    # Critic decides: retry or synthesize
    graph.add_conditional_edges(
        "critic",
        should_retry,
        {
            "retry": "planner",
            "done": "synthesizer"
        }
    )

    # Synthesizer ends the graph
    graph.add_edge("synthesizer", END)

    return graph.compile()


# Single instance used across the app
review_graph = build_graph()