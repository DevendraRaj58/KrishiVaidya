"""
CADI Orchestration — Routing Logic
"""

from typing import Dict, Any

def route_from_plan(state: Dict[str, Any]) -> str:
    """
    Determines next node from 'plan'.
    """
    print(state)
    # For prototype, we go directly to advice if we have enough info
    # In full system, this checks staleness of weather/web/etc.
    if "raw_advisory_text" not in state:
        return "advice"
    return "attribute"
