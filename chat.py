import asyncio
import logging
from src.orchestration.graph import build_cadi_graph
from src.knowledge.graph_loader import build_full_knowledge_graph
from src.attribution.attributed_generator import AttributedGenerator
from src.verification.safety_checker import SafetyChecker
from src.models.llm_client import LLMClient
from dotenv import load_dotenv
import sys

# Suppress debug logs for clean UI
logging.basicConfig(level=logging.ERROR)
load_dotenv()

async def main():
    print("==================================================")
    print("🌿 Welcome to KrishiVaidya CLI (WhatsApp Prototype) 🌿")
    print("==================================================")
    print("Initializing Knowledge Graph and Models... Please wait.\n")
    
    try:
        kg = build_full_knowledge_graph()
        llm_client = LLMClient()
        generator = AttributedGenerator(kg, llm_client=llm_client)
        safety_checker = SafetyChecker(kg)
        cadi_graph = build_cadi_graph()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return

    print("✅ System Ready!\n")
    print("You can start chatting. Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = input("Farmer: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input.strip():
                continue

            print("\nKrishiVaidya is thinking... ⏳")
            
            state = {
                "user_query": user_input,
                "attributed_generator": generator,
                "safety_checker": safety_checker,
                "llm_client": llm_client
            }
            
            try:
                result = await cadi_graph.ainvoke(state)
                
                print("\n==================== RESPONSE ====================")
                if 'advisory' in result and result['advisory']:
                    advisory = result['advisory']
                    
                    # 1. Print Safe / Unsafe Status
                    if advisory.is_safe:
                        print("✅ [VERIFIED SAFE] by CADI Safety Engine")
                    else:
                        print("⚠️ [UNSAFE / MODIFIED] by CADI Safety Engine")
                        
                    # 2. Print Headline
                    print(f"\n{advisory.headline}\n")
                    
                    # 3. Print Claims
                    print("Detailed Advice:")
                    for idx, claim in enumerate(advisory.claims, 1):
                        status = "✅ Grounded" if claim.status == "GROUNDED" else "❓ Ungrounded"
                        print(f" {idx}. {claim.claim.text} [{status}]")
                        
                    # 4. Print Safety Violations if any
                    if advisory.safety_violations:
                        print("\n🚫 Safety Rules Triggered:")
                        for v in advisory.safety_violations:
                            print(f" - {v}")
                            
                    print("==================================================\n")
                else:
                    print("Sorry, I could not generate an advisory for this query.\n")

            except Exception as e:
                if "429" in str(e):
                    print("\n❌ API Quota Exceeded! (Error 429)")
                    print("It looks like you've hit your daily Gemini free tier limit.")
                    print("Please try again tomorrow or upgrade your API key.\n")
                else:
                    print(f"\n❌ Error processing query: {e}\n")

        except KeyboardInterrupt:
            break
            
    print("\nGoodbye! 👋")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
