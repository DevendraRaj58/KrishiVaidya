"""
CADI Orchestration — Nodes (Component ⑦, Part 1)

Defines the LangGraph nodes for the CADI pipeline.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def intake_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts structured fields from free text input.
    """
    logger.info("Running intake_node")
    llm = state.get("llm_client")
    user_query = state.get("user_query", "")
    
    if not llm or not user_query:
        return {"last_node": "intake"}
        
    system_prompt = (
        "Extract agricultural context from the user query. "
        "Return a JSON object with 'crop' (e.g. 'rice', 'wheat', 'cotton') "
        "and 'stage' (e.g. 'germination', 'seedling', 'vegetative', 'flowering', 'fruiting', 'maturity', 'harvesting'). "
        "If not mentioned, use 'unknown'."
    )
    try:
        context = await llm.generate_json(system_prompt, user_query)
    except Exception as e:
        logger.error(f"Error in intake_node: {e}")
        context = {"crop": "unknown", "stage": "unknown"}
        
    return {"context": context, "last_node": "intake"}

async def advice_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates raw advisory text using LLM.
    """
    logger.info("Running advice_node")
    llm = state.get("llm_client")
    user_query = state.get("user_query", "")
    context = state.get("context", {})
    
    if not llm:
        raw_advisory_text = "Apply 50kg/ha Urea. This will help with nitrogen deficiency."
        return {"raw_advisory_text": raw_advisory_text, "last_node": "advice"}
        
    system_prompt = (
        "You are an expert agricultural advisor. Based on the user's query and the current context, "
        "provide a concise, direct, and actionable recommendation (e.g., specific pesticide, fertilizer, or cultural practice). "
        "Do not include disclaimers or conversational filler. State the exact dosage and method if applicable."
    )
    user_prompt = f"Query: {user_query}\nContext: {context}"
    
    try:
        raw_advisory_text = await llm.generate_text(system_prompt, user_prompt)
    except Exception as e:
        logger.error(f"Error in advice_node: {e}")
        raw_advisory_text = "Apply 50kg/ha Urea."
        
    return {"raw_advisory_text": raw_advisory_text, "last_node": "advice"}

async def attribute_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Passes raw advisory through Attribution Engine to get claims and citations.
    """
    logger.info("Running attribute_node")
    generator = state.get("attributed_generator")
    if generator:
        attributed_advisory = await generator.generate(
            raw_advisory_text=state.get("raw_advisory_text", ""),
            headline="Expert Advisory",
            stage=state.get("context", {}).get("stage", "unknown")
        )
        return {"advisory": attributed_advisory, "last_node": "attribute"}
    return {"last_node": "attribute"}

async def safety_check_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Passes attributed advisory through Safety Checker.
    """
    logger.info("Running safety_check_node")
    checker = state.get("safety_checker")
    if checker:
        verdict = checker.check(
            advisory_text=state.get("raw_advisory_text", ""),
            crop_id=state.get("context", {}).get("crop", "unknown"),
            stage=state.get("context", {}).get("stage", "unknown")
        )
        # Update advisory with safety verdict
        advisory = state.get("advisory")
        if advisory:
            advisory.is_safe = verdict.is_safe
            advisory.safety_violations = [v.description for v in verdict.violations]
        return {"safety_verdict": verdict, "advisory": advisory, "last_node": "safety_check"}
    return {"last_node": "safety_check"}

async def plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dummy pass-through node for routing.
    """
    logger.info("Running plan_node")
    return {"last_node": "plan"}
