import asyncio
import logging
from src.orchestration.graph import build_cadi_graph
from src.knowledge.graph_loader import build_full_knowledge_graph
from src.attribution.attributed_generator import AttributedGenerator
from src.verification.safety_checker import SafetyChecker
from src.models.llm_client import LLMClient
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.ERROR)  # Suppress info logs for clarity

async def main():
    print("Testing Cotton Safety Query...")
    kg = build_full_knowledge_graph()
    llm_client = LLMClient()
    generator = AttributedGenerator(kg, llm_client=llm_client)
    safety_checker = SafetyChecker(kg)
    cadi_graph = build_cadi_graph()
    
    user_query = "My cotton crop is flowering. I want to spray Monocrotophos for American Bollworms."
    state = {
        "user_query": user_query,
        "attributed_generator": generator,
        "safety_checker": safety_checker,
        "llm_client": llm_client
    }
    
    print(f"\nUser Query: {user_query}")
    result = await cadi_graph.ainvoke(state)
    
    print("\n--- Final Output ---")
    if 'advisory' in result:
        print(f"Safe: {result['advisory'].is_safe}")
        for claim in result['advisory'].claims:
            print(f" - {claim.claim.text} [{claim.status}]")
    else:
        print("Advisory generation failed.")

if __name__ == "__main__":
    asyncio.run(main())
