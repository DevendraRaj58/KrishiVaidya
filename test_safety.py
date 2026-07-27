import logging
from src.knowledge.graph_loader import build_full_knowledge_graph
from src.verification.safety_checker import SafetyChecker
from src.knowledge.graph_schema import CropStageEnum

logging.basicConfig(level=logging.ERROR)

def run_test():
    kg = build_full_knowledge_graph()
    checker = SafetyChecker(kg)
    
    # Simulate an advisory that mentions monocrotophos for cotton
    advisory_text = "I recommend that you apply Monocrotophos for your cotton crop."
    
    verdict = checker.check(
        advisory_text=advisory_text,
        crop_id="cotton",
        stage=CropStageEnum.FLOWERING,
    )
    
    print("\n--- Safety Verdict ---")
    print(f"Safe: {verdict.is_safe}")
    for v in verdict.violations:
        print(f"[VIOLATION - {v.rule_id}]: {v.description}")
        
    for w in verdict.warnings:
        print(f"[WARNING - {w.rule_id}]: {w.description}")

if __name__ == "__main__":
    run_test()
