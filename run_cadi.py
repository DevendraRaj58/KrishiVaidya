"""
CADI - Phase 1 Integration Runner
"""

import asyncio
import logging
from src.orchestration.graph import build_cadi_graph
from src.knowledge.graph_loader import build_full_knowledge_graph
from src.attribution.attributed_generator import AttributedGenerator
from src.verification.safety_checker import SafetyChecker
from src.models.llm_client import LLMClient
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

async def main():
    print("Initializing CADI Phase 1 Pipeline...")
    
    # 1. Build Knowledge Graph
    kg = build_full_knowledge_graph()
    
    # 2. Initialize Components
    llm_client = LLMClient()
            
    generator = AttributedGenerator(kg, llm_client=llm_client)
    safety_checker = SafetyChecker(kg)
    
    # 3. Build Graph
    cadi_graph = build_cadi_graph()
    
    # 4. Run Pipeline
    user_query = "My rice crop in the vegetative stage has yellowing leaves and circular drying patches. What should I spray?"
    state = {
        "user_query": user_query,
        "attributed_generator": generator,
        "safety_checker": safety_checker,
        "llm_client": llm_client
    }
    
    print(f"\nUser Query: {user_query}")
    print("\nRunning CADI Graph...")
    result = await cadi_graph.ainvoke(state)
    
    print("\n--- Final Advisory ---")
    advisory = result.get("advisory")
    if advisory:
        print(f"Headline: {advisory.headline}")
        print(f"Stage: {advisory.stage}")
        print(f"Safe: {advisory.is_safe}")
        if not advisory.is_safe:
            print(f"Violations: {advisory.safety_violations}")
        for claim in advisory.claims:
            print(f" - {claim.claim.text} [{claim.status}]")
            for ev in claim.evidence:
                print(f"   -> Evidence: {ev.text_snippet}")
                
if __name__ == "__main__":
    asyncio.run(main())
