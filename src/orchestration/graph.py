"""
CADI Orchestration — Main Graph (Component ⑦, Part 2)

Constructs the LangGraph StateGraph.
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Any, Annotated

class CADIState(TypedDict, total=False):
    user_query: str
    context: dict
    raw_advisory_text: str
    advisory: Any
    safety_verdict: Any
    attributed_generator: Any
    safety_checker: Any
    llm_client: Any
    last_node: str

from .nodes import (
    intake_node, plan_node, advice_node,
    attribute_node, safety_check_node
)
from .routing import route_from_plan


def build_cadi_graph() -> StateGraph:
    """
    Constructs the CADI StateGraph.
    """
    workflow = StateGraph(CADIState)

    # Add nodes
    workflow.add_node("intake", intake_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("advice", advice_node)
    workflow.add_node("attribute", attribute_node)
    workflow.add_node("safety_check", safety_check_node)

    # Add edges
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "plan")
    
    # Conditional routing from plan
    workflow.add_conditional_edges(
        "plan",
        route_from_plan,
        {
            "advice": "advice",
            "attribute": "attribute"
        }
    )
    
    workflow.add_edge("advice", "plan") # Loop back to plan
    workflow.add_edge("attribute", "safety_check")
    workflow.add_edge("safety_check", END)

    return workflow.compile()
