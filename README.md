<div align="center">

# 🌿 KrishiVaidya
### *Trusted AI Advisory for Indian Farmers*

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0.7-FF6B35?logo=graphql)](https://github.com/langchain-ai/langgraph)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?logo=telegram)](https://core.telegram.org/bots)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1-412991?logo=openai)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Active Development](https://img.shields.io/badge/Status-Active%20Development-brightgreen)]()

---

> **"India has 140M+ small farmers. 90% lack access to agronomist advice at the right time.  
> Every wrong pesticide decision costs a crop. Every delayed diagnosis can mean a season lost."**

---

</div>

## The Problem

India's agricultural sector faces a critical advisory gap:

- 🌾 **140 million small & marginal farmers** — each managing unique crops, soils, micro-climates
- 🧑‍🌾 **1 agricultural extension officer per 1,000+ farmers** — the human advisory system is overwhelmed
- ❌ **Generic AI chatbots hallucinate** — they confidently recommend wrong pesticides, wrong dosages, wrong timings. A farmer who trusts a hallucinated recommendation can lose an entire season's income.
- 📱 **Farmers already use Telegram & WhatsApp** — the interface problem is already solved. The intelligence layer isn't.

**The core risk: AI agricultural advice that is wrong is worse than no advice at all.**

---

## Our Solution: KrishiVaidya

**KrishiVaidya** is a **Neurosymbolic AI crop advisory system** — a Telegram bot that functions as a personal agronomist for every Indian farmer, with one critical differentiator that no other system has:

> **Every AI-generated recommendation is formally verified against a domain-specific agricultural Knowledge Graph before it reaches the farmer.**

This isn't a chatbot with a disclaimer. This is an AI system with a built-in, rule-based safety engine that can prove (or block) every recommendation it makes.

```
Farmer's Message → LLM Understanding → Advisory Generation
                                              ↓
                              Knowledge Graph Safety Checker
                                              ↓
                        ✅ Verified & Cited    |    ⚠️ Blocked & Reformulated
                                              ↓
                                    Farmer receives advice
```

---

## Architecture: Neurosymbolic AI

KrishiVaidya is not a prompt wrapper. It's a **production-grade agentic AI pipeline** built with an 11-module architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                        TELEGRAM INTERFACE                        │
│            (Multilingual · Image Upload · Location Share)        │
└─────────────────────────────┬───────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     LANGGRAPH AGENTIC PIPELINE                   │
│                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐  │
│  │  Intake  │→  │  Vision  │→  │  Weather │→  │  Web Search │  │
│  │ Extractor│   │Diagnosis │   │   Fetch  │   │  (Tavily)   │  │
│  └──────────┘   └──────────┘   └──────────┘   └─────────────┘  │
│        ↓                                              ↓          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  ADVISORY GENERATOR (GPT-4.1)             │   │
│  │     Context-aware · Crop-stage specific · Multilingual    │   │
│  └──────────────────────────────────────────────────────────┘   │
│        ↓                                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           ATTRIBUTION ENGINE (Component 5)                │   │
│  │  Claim Extraction → Evidence Retrieval → Grounding Score  │   │
│  └──────────────────────────────────────────────────────────┘   │
│        ↓                                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │       ⚠️ SYMBOLIC SAFETY CHECKER (Component 10)           │   │
│  │   Rule Engine · Knowledge Graph Constraints · O(1) lookup │   │
│  │   If SAFE → deliver with citations                        │   │
│  │   If UNSAFE → reformulate OR escalate to human expert     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              AGRICULTURAL KNOWLEDGE GRAPH (NetworkX)             │
│   Crops · Diseases · Pests · Interventions · Safety Constraints  │
│            Gov't Schemes · Regions · ICAR Knowledge              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 🔒 1. Symbolic Safety Verification (The Core Innovation)
A rule-based verification engine sits between the LLM and the farmer. Before any recommendation is delivered, it checks:
- **PHI violations** — Is the harvest window respected for this pesticide?
- **Stage-contraindicated interventions** — Is this chemical banned at this crop stage?
- **Dose overrides** — Does the LLM recommend a dangerous excess dosage?
- **Pollinator toxicity** — Are bee-toxic chemicals being recommended during flowering?
- **Pregnancy/human safety** — Are organophosphate-class chemicals flagged near harvest?

Every violation is **caught, explained, and either fixed or escalated** — never silently delivered.

### 🧠 2. Agricultural Knowledge Graph
Built on NetworkX with ICAR-sourced data:
- **Typed entity nodes**: Crops, Diseases, Pests, Interventions, Safety Constraints, Govt Schemes, Regions
- **Causal directed edges**: `Intervention --treats→ Disease`, `Pest --infects_stage→ CropStage`
- **Multilingual labels**: English, Hindi, Marathi on every entity
- **Temporal constraints**: Government scheme validity windows, seasonal applicability
- **~5K nodes, ~20K edges** across 5 major Indian crops

### 🌍 3. Real-Time Context Fusion
Every advisory synthesizes **four live data streams**:
- 🌦️ **Weather** (OpenWeather One Call 3.0) — actual conditions, forecasts, extreme weather alerts
- 🔍 **Web Search** (Tavily) — latest pest outbreak news, current mandi prices
- 📸 **Vision Diagnosis** (GPT-4 Vision) — crop disease detection from a farmer's phone photo
- 📍 **Location-aware** — advice calibrated to the farmer's exact geography and soil type

### 💬 4. True Multilingual Support
- English, Hindi, Marathi — **full conversational fluency**, not just keyword translation
- Farmers set their language once; the bot responds naturally in that language forever
- Works with voice-to-text compatible input formats

### 📊 5. Attribution & Grounding Score
Every recommendation includes:
- Citation to the specific ICAR bulletin or KG node it's grounded in
- A **grounding score** (0–1) showing how well the advice is backed by verified knowledge
- `GROUNDED` / `WEAKLY_GROUNDED` / `UNGROUNDED` tags per claim
- Human expert escalation flag when confidence is below threshold

### 👨‍🌾 6. Persistent Farmer Context
- MySQL-backed session store with farmer profile: name, crop, stage, land size, location, soil type
- 24-hour daily digest — proactive advisory pushed to the farmer every morning
- One-tap action buttons: "Show Market Prices", "Show Govt Schemes", "Crop Recommendation"

---

## What Makes KrishiVaidya Different

| Feature | Generic AI (ChatGPT/Gemini) | Existing Agri Apps | **KrishiVaidya** |
|---|---|---|---|
| Safety verification before delivery | ❌ | ❌ | ✅ Rule-based KG engine |
| Domain knowledge grounding | ❌ (hallucination risk) | Partial | ✅ Cited ICAR sources |
| Live weather integration | ❌ | Some | ✅ Real-time fusion |
| Crop photo diagnosis | Limited | Some | ✅ GPT-4 Vision |
| Multilingual (Hi/Mr) | Partial | Partial | ✅ Full conversational |
| Farmer persistent profile | ❌ | Registration-heavy | ✅ Auto-built via chat |
| Works on existing platform | ❌ | App download required | ✅ Telegram — no install |
| Govt scheme awareness | ❌ | Partial | ✅ Live search + KG |
| Human escalation trigger | ❌ | ❌ | ✅ Auto-flagged |

> **No existing system interposes a symbolic, knowledge-grounded safety verification layer between an LLM agricultural advisor and the farmer. KrishiVaidya is the first to do this.**

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Orchestration** | LangGraph 1.0.7 | Agentic multi-node pipeline with state management |
| **LLM** | OpenAI GPT-4.1 / GPT-4o-mini | Advisory generation, intake extraction, vision |
| **Knowledge Graph** | NetworkX + custom schema | ICAR-grounded agricultural ontology |
| **Web Search** | Tavily API | Live pest news, market prices, scheme updates |
| **Weather** | OpenWeather One Call 3.0 | Real-time conditions + 7-day forecasts |
| **Interface** | python-telegram-bot 22.6 | Farmer-facing Telegram bot |
| **Database** | MySQL + SQLAlchemy | Persistent farmer sessions, image records |
| **Validation** | Pydantic v2 | Strict data models across all pipeline stages |
| **Language** | Python 3.11+ | Async-first architecture |

---

## Project Structure

```
KrishiVaidya/
├── src/
│   ├── app/                    # Core Telegram bot & LangGraph pipeline
│   │   ├── graph.py            # Main agentic graph (12 nodes)
│   │   ├── telegram_bot.py     # Bot handler, commands, UI
│   │   ├── tools.py            # Weather, web search, geocoding
│   │   ├── models.py           # Pydantic data models (GraphState etc.)
│   │   ├── store.py            # Session persistence (JSON/MySQL)
│   │   ├── db.py               # SQLAlchemy database layer
│   │   └── config.py           # Environment-based settings
│   │
│   ├── knowledge/              # Agricultural Knowledge Graph
│   │   ├── graph_schema.py     # Entity & relation type definitions
│   │   ├── graph.py            # AgriKnowledgeGraph engine (NetworkX)
│   │   └── graph_loader.py     # ICAR data loader (5 crops, full ontology)
│   │
│   ├── attribution/            # Evidence grounding & citation engine
│   │   ├── claim_extractor.py  # LLM-based atomic claim decomposition
│   │   ├── evidence_retriever.py # KG subgraph evidence retrieval
│   │   ├── grounding_scorer.py # Claim grounding score calculator
│   │   └── attributed_generator.py # Full attribution pipeline
│   │
│   ├── verification/           # Safety rule engine
│   │   └── safety_checker.py   # Symbolic constraint verification (10 rule classes)
│   │
│   ├── orchestration/          # CADI pipeline orchestration
│   │   ├── graph.py            # LangGraph pipeline definition
│   │   ├── nodes.py            # Pipeline node implementations
│   │   └── routing.py          # Conditional routing logic
│   │
│   ├── models/                 # Shared data models
│   │   ├── advisory.py         # Advisory, Claim, Citation models
│   │   └── llm_client.py       # LLM abstraction layer
│   │
│   └── interface/              # Output formatting
│       └── formatter.py        # Response formatting utilities
│
├── run.py                      # Main entrypoint — starts Telegram bot
├── demo.py                     # Panel demo CLI (no API needed in --demo mode)
├── chat.py                     # CLI chat interface for testing
├── run_cadi.py                 # CADI pipeline runner for development
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
└── .gitignore
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- MySQL (XAMPP or any MySQL server)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenAI API Key
- Tavily API Key
- OpenWeather API Key

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/KrishiVaidya.git
cd KrishiVaidya

python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

Key variables to set:
```env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
TAVILY_API_KEY=tvly-...
OPENWEATHER_API_KEY=...
MYSQL_DATABASE=krishivaidya
```

### 3. Start the Bot

```bash
python run.py
```

### 4. Try the Demo (No API keys needed)

```bash
# Curated panel demo — works without any API
python demo.py --demo

# Safety engine demo — shows blocked unsafe advisories
python demo.py --safety
```

---

## Example Interaction

```
Farmer:  My cotton in Yavatmal is at flowering stage.
         Leaves have yellow spots and small holes. Very urgent.

KrishiVaidya:

  ✅ VERIFIED SAFE by KrishiVaidya Safety Engine

  🚨 Cotton Jassid Alert — Immediate Action Required
  ─────────────────────────────────────────────────
  Actions:
    1. Spray Imidacloprid 17.8 SL @ 0.3 ml/L (foliar, evening hours)
    2. Inspect underside of leaves for Jassid nymphs
    3. Maintain 7-day gap before next chemical spray

  Watch Out:
    • Do NOT spray during pollinator activity (8 AM–5 PM)
    • Check for secondary Whitefly infestation

  Safety Notes:
    • Pre-Harvest Interval: 21 days — do not harvest before this

  Sources: ICAR-CICR Cotton Production Technology Bulletin, 2020
  Confidence: HIGH  |  Grounding Score: 0.87
```

---

## Currently In Development

We are actively building the next major phase of KrishiVaidya:

### 🔧 In Progress Right Now
- **Voice Message Support** — farmers send voice notes; Whisper transcribes before pipeline processing
- **WhatsApp Integration** — expanding to WhatsApp Business API (Meta Cloud API)
- **Admin Dashboard** — real-time analytics: query volume, safety violations caught, crop/region heatmaps

### 📅 Coming Next
- **Full Crop Coverage** — expanding from 5 to 20+ Indian crops (Rice, Cotton, Wheat, Tomato, Soybean currently supported)
- **District-level Pest Outbreak Alerts** — if 10+ farmers in a district report the same symptoms, push a broadcast alert to everyone in that region
- **KVK Integration** — automatic escalation to nearest Krishi Vigyan Kendra when `needs_human_review=True`
- **Mandi Price Predictions** — ML-based price forecasting 7–14 days ahead for harvest timing decisions
- **On-Device Image Preprocessing** — compress/normalize crop photos client-side to reduce latency and API cost

### 🔬 Research Track
- Formal publication of the Neurosymbolic safety verification architecture
- Benchmark dataset for agricultural advisory hallucination detection
- Evaluation framework for comparing AI agricultural advisors on safety, accuracy, and cultural appropriateness

---

## Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for India's 140 million farmers**

*KrishiVaidya — Where AI Meets Agronomic Wisdom*

</div>
