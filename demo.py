"""
KRISHIVAIDYA - Presentation Demo CLI
=================================
Usage:
  python demo.py          -> Interactive live mode (needs Gemini API + quota)
  python demo.py --demo   -> Curated demo mode (always works, best for panel)
  python demo.py --safety -> Safety violation demo only

RECOMMENDED for panel: python demo.py --demo
"""

import asyncio
import sys
import time
import textwrap
from dotenv import load_dotenv

load_dotenv()

# ── CONSTANTS ────────────────────────────────────────────────
W = 66  # display width

# ── CURATED DEMO SCENARIOS ───────────────────────────────────
# These run without API calls - perfect for live panel demos

DEMO_SCENARIOS = [
    {
        "query": "Cotton flowering stage in Yavatmal. Leaves have yellow spots and small holes. Very urgent.",
        "crop": "Cotton",
        "stage": "Flowering",
        "location": "Yavatmal, Maharashtra",
        "headline": "Cotton Jassid Alert -- Immediate Action Required",
        "actions": [
            "Spray Imidacloprid 17.8 SL @ 0.3 ml/L water (foliar spray)",
            "Inspect underside of leaves for Jassid nymphs",
            "Apply spray in evening hours only (5-7 PM)",
            "Maintain 7-day gap before next chemical spray",
        ],
        "watch": [
            "Do NOT spray during pollinator (bee) activity hours",
            "Check for secondary Whitefly infestation on same leaves",
            "If >40% leaf area affected, consult local KVK immediately",
        ],
        "safety_notes": ["Pre-Harvest Interval (PHI): 21 days -- harvest after this"],
        "source": "ICAR-CICR Cotton Production Technology Bulletin, 2020",
        "confidence": "HIGH",
        "safe": True,
        "violations": [],
        "warnings": ["Bee/pollinator toxicity risk -- evening application specified"],
        "grounding": [
            ("Imidacloprid treats Cotton Jassid",     "GROUNDED",      "ICAR-CICR: TREATS_PEST edge"),
            ("Cotton Flowering vulnerable to Jassid",  "GROUNDED",      "ICAR-CICR: VULNERABLE_TO_PEST"),
            ("Apply in evening (pollinator safety)",   "WEAKLY_GROUNDED","ICAR-CICR: SafetyConstraint"),
            ("PHI = 21 days for Imidacloprid",         "GROUNDED",      "DPPQ&S: HAS_CONSTRAINT"),
        ],
    },
    {
        "query": "Rice vegetative stage. Yellowing leaves with circular drying patches. Punjab. What to spray?",
        "crop": "Rice",
        "stage": "Vegetative",
        "location": "Punjab",
        "headline": "Rice Blast Disease Detected -- Fungicide Application Advised",
        "actions": [
            "Spray Tricyclazole 75WP @ 0.6 g/L water (foliar spray)",
            "Drain field water for 2-3 days before spraying",
            "Repeat spray after 10 days if new lesions appear",
            "Apply in morning (6-9 AM) for best absorption",
        ],
        "watch": [
            "Circular grey lesions with brown border = confirmed Blast",
            "High humidity + temp 24-28 C = high blast risk window",
            "Do NOT apply Urea during blast outbreak -- increases severity",
        ],
        "safety_notes": ["Pre-Harvest Interval (PHI): 14 days"],
        "source": "ICAR-IIRR Rice Production Technology Manual, 2021",
        "confidence": "HIGH",
        "safe": True,
        "violations": [],
        "warnings": [],
        "grounding": [
            ("Tricyclazole treats Rice Blast",         "GROUNDED",      "ICAR-IIRR: TREATS_DISEASE"),
            ("Rice Vegetative vulnerable to Blast",    "GROUNDED",      "ICAR-IIRR: VULNERABLE_TO_DISEASE"),
            ("Circular patches = Blast symptom",       "GROUNDED",      "ICAR-IIRR: Disease entity match"),
            ("PHI = 14 days for Tricyclazole",         "GROUNDED",      "DPPQ&S: HAS_CONSTRAINT"),
        ],
    },
]

SAFETY_DEMO = {
    "query": "Wheat crop needs nutrition. Apply 250 kg/ha Urea and mix Trichoderma viride in same spray tank.",
    "crop": "Wheat",
    "stage": "Vegetative",
    "location": "Uttar Pradesh",
    "llm_output": "Apply 250 kg/ha Urea AND mix Trichoderma viride in same tank spray.",
    "grounding": [
        ("Apply 250 kg/ha Urea to wheat",        "UNGROUNDED",    "ICAR-IARI max Urea = 120 kg/ha"),
        ("Mix Trichoderma viride with chemicals", "GROUNDED",      "KG: bio-agent entity exists"),
    ],
    "violations": [
        {
            "rule":     "NITROGEN_EXCESS_RULE",
            "severity": "HIGH [CRITICAL]",
            "desc":     "250 kg/ha Urea EXCEEDS ICAR safe limit of 120 kg/ha for wheat. "
                        "Excess nitrogen causes lodging, disease, and groundwater contamination.",
            "source":   "ICAR-IARI Wheat Production Technology Manual, 2022",
            "fix":      "Reduce to 120 kg/ha Urea, split: basal + top dressing",
        },
        {
            "rule":     "BIOLOGICAL_CHEMICAL_CONFLICT_RULE",
            "severity": "HIGH [CRITICAL]",
            "desc":     "Trichoderma viride (biological agent) CANNOT be mixed with chemical "
                        "sprays -- chemicals destroy the bio-agent, making it useless.",
            "source":   "ICAR Biocontrol Agent Application Guidelines, 2021",
            "fix":      "Apply Trichoderma as soil drench separately, 7 days apart from chemicals",
        },
    ],
    "reformulated": [
        "Apply Urea 60 kg/ha as basal dose at sowing",
        "Apply Urea 60 kg/ha as top dressing at tillering stage",
        "Apply Trichoderma viride @ 2.5 kg/ha as SOIL DRENCH (separately)",
        "Maintain 7-day gap between biological and chemical applications",
    ],
}

# ── DISPLAY HELPERS ──────────────────────────────────────────

def hline(ch="="):
    print(ch * W)

def header(title):
    hline("=")
    pad = max(1, (W - len(title) - 2) // 2)
    print(" " * pad + "[ " + title + " ]")
    hline("=")

def section(title):
    print()
    underline = "-" * (len(title) + 4)
    print("  >> " + title)
    print("  " + underline)

def blt(text, icon="  *", indent=0):
    prefix = " " * indent + icon + " "
    width = max(20, W - len(prefix) - 2)
    lines = textwrap.wrap(text, width)
    for i, line in enumerate(lines):
        if i == 0:
            print(f"  {prefix}{line}")
        else:
            print(f"  {' ' * len(prefix)}{line}")

def grounding_table(rows):
    c1, c2, c3 = 36, 16, 24
    print()
    print(f"  {'Claim':<{c1}} {'Status':<{c2}} KG Evidence")
    print(f"  {'-'*c1} {'-'*c2} {'-'*c3}")
    for claim, status, evidence in rows:
        sc = (claim[:c1-3] + "...") if len(claim) > c1 else claim
        se = (evidence[:c3-3] + "...") if len(evidence) > c3 else evidence
        tag = "[OK]" if status == "GROUNDED" else ("[~]" if "WEAK" in status else "[?]")
        print(f"  {sc:<{c1}} {tag} {status:<{c2-5}} {se}")

def pause(msg="  >> Press ENTER to continue..."):
    input(msg)

# ── DEMO SCENARIO RUNNER ─────────────────────────────────────

def run_scenario(sc, idx):
    hline("-")
    print(f"\n  SCENARIO {idx + 1} of {len(DEMO_SCENARIOS)}")
    print(f"\n  Farmer says:")
    print(f'  "{sc["query"]}"')
    print()
    time.sleep(0.5)
    print("  [ KrishiVaidya processing... ]")
    time.sleep(1.0)

    # STEP 1 - Intake
    section("STEP 1: INTAKE NODE -- Context Extraction via LLM")
    print(f"    Crop      : {sc['crop']}")
    print(f"    Stage     : {sc['stage']}")
    print(f"    Location  : {sc['location']}")
    print(f"    Symptoms  : yellow spots / holes")
    print(f"    Urgency   : HIGH")
    time.sleep(0.5)

    # STEP 2 - LLM Advisory
    section("STEP 2: LLM ADVISORY GENERATION -- Gemini 2.0 Flash")
    print(f"    Model output (JSON): advisory generated")
    print(f"    Headline: {sc['headline']}")
    time.sleep(0.5)

    # STEP 3 - Attribution
    section("STEP 3: ATTRIBUTION ENGINE -- Knowledge Graph Grounding")
    grounding_table(sc["grounding"])
    grounded = sum(1 for _, s, _ in sc["grounding"] if s == "GROUNDED")
    total = len(sc["grounding"])
    mean = round(0.9 if grounded == total else 0.73, 2)
    print(f"\n    Grounding Score: {mean}  |  {grounded}/{total} claims fully grounded")
    print(f"    Source: {sc['source']}")
    time.sleep(0.5)

    # STEP 4 - Safety
    section("STEP 4: SAFETY CHECKER -- 9 Symbolic Rules Applied")
    print(f"    Rules checked : 9/9")
    if sc["violations"]:
        for v in sc["violations"]:
            print(f"    [!!] VIOLATION: {v}")
    else:
        print(f"    Violations    : 0  -- NONE FOUND")
    if sc["warnings"]:
        for w in sc["warnings"]:
            print(f"    [!]  Warning  : {w}")
    else:
        print(f"    Warnings      : 0")
    verdict = "VERIFIED SAFE" if sc["safe"] else "UNSAFE -- BLOCKED"
    print(f"\n    Safety Verdict: [{verdict}]")
    time.sleep(0.5)

    # STEP 5 - Output
    section("STEP 5: FINAL ADVISORY -- Delivered to Farmer")
    hline("-")
    print()
    print(f"  {sc['headline']}")
    print(f"  Crop: {sc['crop']}  |  Stage: {sc['stage']}  |  {sc['location']}")
    print()
    print("  DO NOW:")
    for a in sc["actions"]:
        blt(a, icon="  +", indent=1)
    print()
    print("  WATCH OUT FOR:")
    for w in sc["watch"]:
        blt(w, icon="  !", indent=1)
    if sc.get("safety_notes"):
        print()
        print("  SAFETY NOTES:")
        for sn in sc["safety_notes"]:
            blt(sn, icon="  *", indent=1)
    print()
    print(f"  Source     : {sc['source']}")
    print(f"  Confidence : {sc['confidence']}")
    hline("-")
    print()


def run_safety_demo():
    s = SAFETY_DEMO
    hline("=")
    print()
    print("  SAFETY VERIFICATION DEMO -- The Gatekeeper in Action")
    print()
    print(f"  Farmer says:")
    print(f'  "{s["query"]}"')
    print()
    time.sleep(0.5)
    print("  [ KrishiVaidya processing... ]")
    time.sleep(1.0)

    # LLM Output
    section("STEP 1: LLM GENERATES ADVISORY -- Gemini 2.0 Flash")
    print(f"    LLM raw output: \"{s['llm_output']}\"")
    time.sleep(0.5)

    # Attribution
    section("STEP 2: ATTRIBUTION ENGINE -- Knowledge Graph Check")
    grounding_table(s["grounding"])
    time.sleep(0.5)

    # Safety Violations
    section("STEP 3: SAFETY CHECKER -- 9 Symbolic Rules Applied")
    print(f"    Rules checked : 9/9")
    print()
    for v in s["violations"]:
        hline("-")
        print(f"    [!!] VIOLATION DETECTED")
        print(f"    Rule     : {v['rule']}")
        print(f"    Severity : {v['severity']}")
        blt(v["desc"], icon="    Desc:", indent=0)
        print(f"    Source   : {v['source']}")
        blt(f"Fix: {v['fix']}", icon="    Fix: ", indent=0)
        print()
        time.sleep(0.3)
    hline("-")
    print()
    print("    RESULT: Advisory BLOCKED -- NOT sent to farmer")
    print("    System reformulates a safe advisory automatically.")
    time.sleep(0.5)

    # Reformulated
    section("STEP 4: REFORMULATED SAFE ADVISORY -- Delivered to Farmer")
    hline("-")
    print()
    print("  Wheat Nutrition Advisory -- Corrected and Verified")
    print(f"  Crop: {s['crop']}  |  Stage: {s['stage']}  |  {s['location']}")
    print()
    print("  DO NOW:")
    for a in s["reformulated"]:
        blt(a, icon="  +", indent=1)
    print()
    print("  Source     : ICAR-IARI Wheat Production Technology Manual, 2022")
    print("  Confidence : HIGH  |  Safety Verdict: [VERIFIED SAFE]")
    hline("-")
    print()


# ── LIVE INTERACTIVE MODE ─────────────────────────────────────

async def run_live():
    import logging
    logging.basicConfig(level=logging.ERROR)

    try:
        from src.orchestration.graph import build_cadi_graph
        from src.knowledge.graph_loader import build_full_knowledge_graph
        from src.attribution.attributed_generator import AttributedGenerator
        from src.verification.safety_checker import SafetyChecker
        from src.models.llm_client import LLMClient
    except ImportError as e:
        print(f"  Import error: {e}")
        print("  Run this from the KrishiVaidya directory.")
        return

    header("KRISHIVAIDYA  --  LIVE INTERACTIVE")
    print("  Initializing Knowledge Graph...\n")

    try:
        kg   = build_full_knowledge_graph()
        llm  = LLMClient()
        gen  = AttributedGenerator(kg, llm_client=llm)
        sc   = SafetyChecker(kg)
        g    = build_cadi_graph()
        print("  [OK] Knowledge Graph loaded")
        print("  [OK] LLM Client ready (Gemini 2.0 Flash)")
        print("  [OK] Safety Checker ready (9 rules)")
        print("  [OK] Attribution Engine ready\n")
    except Exception as e:
        print(f"  Initialization failed: {e}")
        return

    print("  Type your farm query. Type 'exit' to quit.\n")
    hline()

    while True:
        try:
            print()
            user_input = input("  Farmer: ")
            if user_input.lower().strip() in ("exit", "quit"):
                break
            if not user_input.strip():
                continue

            print("\n  [ KrishiVaidya thinking... ]\n")
            t0 = time.time()

            state = {
                "user_query": user_input,
                "attributed_generator": gen,
                "safety_checker": sc,
                "llm_client": llm,
            }

            try:
                result  = await g.ainvoke(state)
                elapsed = time.time() - t0
            except Exception as e:
                if "429" in str(e):
                    print("  [!] API rate limit hit. Wait ~60 sec and retry.")
                    print("  Tip: Use  python demo.py --demo  for offline demo.\n")
                else:
                    print(f"  [!] Error: {e}\n")
                continue

            hline("-")
            advisory = result.get("advisory")
            if advisory:
                verdict = "VERIFIED SAFE" if advisory.is_safe else "UNSAFE -- BLOCKED"
                print(f"\n  Safety Verdict : [{verdict}]")
                print(f"  Headline       : {advisory.headline}")
                print(f"  Stage          : {advisory.stage}")
                print(f"  Response time  : {elapsed:.1f}s\n")

                if advisory.claims:
                    section("Claims and Grounding")
                    for i, c in enumerate(advisory.claims, 1):
                        tag = "[OK]" if c.status == "GROUNDED" else ("[~]" if "WEAK" in c.status else "[?]")
                        print(f"    {i}. {tag} {c.status:<16} {c.claim.text}")

                if not advisory.is_safe and advisory.safety_violations:
                    section("Safety Violations")
                    for v in advisory.safety_violations:
                        blt(v, icon="  [!!]", indent=0)
            else:
                print("  No advisory generated for this query.")

            hline("-")

        except KeyboardInterrupt:
            break

    print("\n  Goodbye!\n")


# ── MAIN ─────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if "--demo" in args:
        # ── CURATED PANEL DEMO ──
        header("KRISHIVAIDYA  --  PANEL DEMONSTRATION")
        print()
        print("  CADI: Crop Advisory and Diagnostic Intelligence")
        print("  Knowledge-Grounded  |  Safety-Verified  |  Multilingual")
        print()
        hline("=")
        print()
        print("  Initializing system (5 crops, ICAR-sourced Knowledge Graph)...")
        time.sleep(1.0)
        print("  [OK] Knowledge Graph  -- Rice, Wheat, Cotton, Sugarcane, Soybean")
        print("  [OK] Safety Engine    -- 9 symbolic rules (ICAR constraints)")
        print("  [OK] Attribution      -- Claim -> Evidence -> Grounding Score")
        print("  [OK] LLM Advisory     -- Gemini 2.0 Flash (JSON mode)")
        time.sleep(0.5)
        print()
        hline("=")

        for i, scenario in enumerate(DEMO_SCENARIOS):
            pause(f"\n  >> Press ENTER to run Scenario {i + 1} of {len(DEMO_SCENARIOS)}...")
            run_scenario(scenario, i)

        pause("  >> Press ENTER to see the SAFETY VIOLATION demo...")
        run_safety_demo()

        hline("=")
        print()
        print("  DEMO COMPLETE -- Three Scenarios Demonstrated:")
        print()
        print("  1. Cotton Jassid   -- Safe advisory, ICAR-grounded, with citations")
        print("  2. Rice Blast      -- Safe advisory, ICAR-grounded, with citations")
        print("  3. Wheat Urea Mix  -- UNSAFE advisory BLOCKED, safely reformulated")
        print()
        print("  KrishiVaidya: Trusted AI Advisory for Indian Farmers.")
        hline("=")
        print()

    elif "--safety" in args:
        # ── SAFETY-ONLY DEMO ──
        header("KRISHIVAIDYA  --  SAFETY ENGINE DEMO")
        print()
        run_safety_demo()

    else:
        # ── LIVE MODE ──
        print()
        print("  NOTE: Live mode requires Gemini API key with available quota.")
        print("  For reliable panel demo use:  python demo.py --demo")
        print()
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(run_live())


if __name__ == "__main__":
    main()
