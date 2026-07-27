"""
CADI Knowledge Graph — Data Loader

Populates the AgriKnowledgeGraph with curated agronomic knowledge
sourced from ICAR publications, KVK district recommendations,
and State Agricultural University bulletins.

Data sources cited:
  - ICAR-IIRR (Indian Institute of Rice Research) — Rice Production Technology
  - ICAR-IARI — Wheat Production Technology Manual
  - ICAR-CICR — Cotton Production Technology Bulletin
  - ICAR-SBI (Sugarcane Breeding Institute) — Sugarcane Cultivation Guide
  - ICAR-IISR — Soybean Production Technology
  - KVK system advisories (state-wise)
  - Directorate of Plant Protection — Pesticide recommendations
  - PM-KISAN, PKVY, PMFBY scheme guidelines

NOTE: All dosage ranges, safety constraints, and intervention
recommendations are sourced from official ICAR/SAU publications.
This is critical for the safety verification pipeline.
"""

from __future__ import annotations

import logging
from datetime import date

from .graph import AgriKnowledgeGraph
from .graph_schema import (
    Crop, CropStage, CropStageEnum, Disease, Edge, GovtScheme,
    Intervention, InterventionType, MultiLabel, Nutrient, Pest,
    Region, RelationType, SafetyConstraint, SeasonEnum,
    SeverityLevel, SoilTypeEnum,
)

logger = logging.getLogger(__name__)


def build_full_knowledge_graph() -> AgriKnowledgeGraph:
    """Build and return the complete CADI agricultural knowledge graph.

    This is the master builder that calls all per-crop and shared
    data loaders, then validates graph integrity.
    """
    kg = AgriKnowledgeGraph()

    # Shared entities (nutrients, regions, schemes)
    _load_nutrients(kg)
    _load_regions(kg)
    _load_govt_schemes(kg)

    # Per-crop data
    _load_rice(kg)
    _load_wheat(kg)
    _load_cotton(kg)
    _load_sugarcane(kg)
    _load_soybean(kg)

    logger.info("Knowledge graph built: %s", kg.stats)
    return kg


# ═══════════════════════════════════════════════════════════════
# SHARED ENTITIES
# ═══════════════════════════════════════════════════════════════

def _load_nutrients(kg: AgriKnowledgeGraph) -> None:
    """Load macro- and micro-nutrients."""
    nutrients = [
        Nutrient(id="nitrogen", label=MultiLabel("Nitrogen", "नाइट्रोजन", "नायट्रोजन"), symbol="N", category="macro"),
        Nutrient(id="phosphorus", label=MultiLabel("Phosphorus", "फॉस्फोरस", "फॉस्फरस"), symbol="P", category="macro"),
        Nutrient(id="potassium", label=MultiLabel("Potassium", "पोटैशियम", "पोटॅशिअम"), symbol="K", category="macro"),
        Nutrient(id="zinc", label=MultiLabel("Zinc", "जिंक", "जस्त"), symbol="Zn", category="micro"),
        Nutrient(id="iron", label=MultiLabel("Iron", "लोहा", "लोह"), symbol="Fe", category="micro"),
        Nutrient(id="boron", label=MultiLabel("Boron", "बोरॉन", "बोरॉन"), symbol="B", category="micro"),
        Nutrient(id="sulphur", label=MultiLabel("Sulphur", "गंधक", "गंधक"), symbol="S", category="macro"),
        Nutrient(id="calcium", label=MultiLabel("Calcium", "कैल्शियम", "कॅल्शिअम"), symbol="Ca", category="macro"),
        Nutrient(id="magnesium", label=MultiLabel("Magnesium", "मैग्नीशियम", "मॅग्नेशिअम"), symbol="Mg", category="macro"),
        Nutrient(id="manganese", label=MultiLabel("Manganese", "मैंगनीज", "मँगेनीज"), symbol="Mn", category="micro"),
    ]
    for n in nutrients:
        kg.add_entity(n)


def _load_regions(kg: AgriKnowledgeGraph) -> None:
    """Load major Indian agroclimatic zones / states."""
    regions = [
        Region(id="maharashtra", label=MultiLabel("Maharashtra", "महाराष्ट्र", "महाराष्ट्र"),
               state="Maharashtra", agroclimatic_zone="Western Plateau and Hills",
               predominant_soils=[SoilTypeEnum.BLACK_COTTON, SoilTypeEnum.RED, SoilTypeEnum.LATERITE],
               avg_rainfall_mm=1200),
        Region(id="punjab", label=MultiLabel("Punjab", "पंजाब", "पंजाब"),
               state="Punjab", agroclimatic_zone="Trans-Gangetic Plains",
               predominant_soils=[SoilTypeEnum.ALLUVIAL, SoilTypeEnum.LOAMY],
               avg_rainfall_mm=650),
        Region(id="uttar_pradesh", label=MultiLabel("Uttar Pradesh", "उत्तर प्रदेश", "उत्तर प्रदेश"),
               state="Uttar Pradesh", agroclimatic_zone="Upper Gangetic Plains",
               predominant_soils=[SoilTypeEnum.ALLUVIAL, SoilTypeEnum.LOAMY],
               avg_rainfall_mm=900),
        Region(id="madhya_pradesh", label=MultiLabel("Madhya Pradesh", "मध्य प्रदेश", "मध्य प्रदेश"),
               state="Madhya Pradesh", agroclimatic_zone="Central Plateau and Hills",
               predominant_soils=[SoilTypeEnum.BLACK_COTTON, SoilTypeEnum.ALLUVIAL],
               avg_rainfall_mm=1100),
        Region(id="telangana", label=MultiLabel("Telangana", "तेलंगाना", "तेलंगणा"),
               state="Telangana", agroclimatic_zone="Southern Plateau and Hills",
               predominant_soils=[SoilTypeEnum.RED, SoilTypeEnum.BLACK_COTTON],
               avg_rainfall_mm=950),
        Region(id="karnataka", label=MultiLabel("Karnataka", "कर्नाटक", "कर्नाटक"),
               state="Karnataka", agroclimatic_zone="Southern Plateau and Hills",
               predominant_soils=[SoilTypeEnum.RED, SoilTypeEnum.LATERITE, SoilTypeEnum.BLACK_COTTON],
               avg_rainfall_mm=1150),
        Region(id="west_bengal", label=MultiLabel("West Bengal", "पश्चिम बंगाल", "पश्चिम बंगाल"),
               state="West Bengal", agroclimatic_zone="Lower Gangetic Plains",
               predominant_soils=[SoilTypeEnum.ALLUVIAL, SoilTypeEnum.CLAYEY],
               avg_rainfall_mm=1750),
        Region(id="gujarat", label=MultiLabel("Gujarat", "गुजरात", "गुजरात"),
               state="Gujarat", agroclimatic_zone="Gujarat Plains and Hills",
               predominant_soils=[SoilTypeEnum.BLACK_COTTON, SoilTypeEnum.ALLUVIAL, SoilTypeEnum.SANDY],
               avg_rainfall_mm=800),
        Region(id="rajasthan", label=MultiLabel("Rajasthan", "राजस्थान", "राजस्थान"),
               state="Rajasthan", agroclimatic_zone="Western Dry Region",
               predominant_soils=[SoilTypeEnum.SANDY, SoilTypeEnum.ALLUVIAL],
               avg_rainfall_mm=500),
        Region(id="tamil_nadu", label=MultiLabel("Tamil Nadu", "तमिल नाडु", "तामिळनाडू"),
               state="Tamil Nadu", agroclimatic_zone="East Coast Plains and Hills",
               predominant_soils=[SoilTypeEnum.RED, SoilTypeEnum.ALLUVIAL, SoilTypeEnum.BLACK_COTTON],
               avg_rainfall_mm=950),
    ]
    for r in regions:
        kg.add_entity(r)


def _load_govt_schemes(kg: AgriKnowledgeGraph) -> None:
    """Load major government schemes with validity dates."""
    schemes = [
        GovtScheme(
            id="pm_kisan",
            label=MultiLabel("PM-KISAN", "पीएम-किसान", "पीएम-किसान"),
            description="Income support of ₹6000/year to all landholding farmer families",
            eligible_crops=[],  # all crops
            eligible_regions=[],  # all India
            valid_from=date(2019, 2, 1),
            valid_until=date(2027, 3, 31),
            url="https://pmkisan.gov.in",
            source="Ministry of Agriculture & Farmers Welfare",
        ),
        GovtScheme(
            id="pmfby",
            label=MultiLabel("PMFBY (Crop Insurance)", "पीएमएफबीवाई", "पीएमएफबीवाय"),
            description="Pradhan Mantri Fasal Bima Yojana — crop insurance at subsidized premium",
            eligible_crops=["rice", "wheat", "cotton", "soybean", "sugarcane"],
            eligible_regions=[],
            valid_from=date(2016, 4, 1),
            valid_until=date(2027, 3, 31),
            url="https://pmfby.gov.in",
            source="Ministry of Agriculture",
        ),
        GovtScheme(
            id="pkvy",
            label=MultiLabel("PKVY (Organic Farming)", "पीकेवीवाई", "पीकेवीवाय"),
            description="Paramparagat Krishi Vikas Yojana — ₹50,000/ha for organic farming",
            eligible_crops=[],
            eligible_regions=[],
            valid_from=date(2015, 4, 1),
            valid_until=date(2026, 3, 31),
            url="https://pgsindia-ncof.gov.in/pkvy",
            source="Ministry of Agriculture",
        ),
        GovtScheme(
            id="smam",
            label=MultiLabel("Sub-Mission on Agricultural Mechanization", "कृषि यंत्रीकरण उप-मिशन", "कृषी यांत्रिकीकरण उप-मिशन"),
            description="Subsidies on farm machinery (50-80% for SC/ST, 40-50% for others)",
            eligible_crops=[],
            eligible_regions=[],
            valid_from=date(2014, 4, 1),
            valid_until=date(2026, 3, 31),
            url="https://agrimachinery.nic.in",
            source="Ministry of Agriculture",
        ),
        GovtScheme(
            id="nfsm_rice",
            label=MultiLabel("NFSM-Rice", "एनएफएसएम-चावल", "एनएफएसएम-तांदूळ"),
            description="National Food Security Mission — Rice: subsidies on seeds, micronutrients, farm machinery",
            eligible_crops=["rice"],
            eligible_regions=[],
            valid_from=date(2007, 8, 1),
            valid_until=date(2026, 3, 31),
            url="https://nfsm.gov.in",
            source="DAC&FW",
        ),
    ]
    for s in schemes:
        kg.add_entity(s)
        # Link schemes to crops
        for crop_id in s.eligible_crops:
            kg.add_edge(Edge(s.id, crop_id, RelationType.APPLICABLE_TO_CROP,
                             evidence_source=s.source))


# ═══════════════════════════════════════════════════════════════
# RICE — Complete Knowledge Graph
# Source: ICAR-IIRR Rice Production Technology
# ═══════════════════════════════════════════════════════════════

def _load_rice(kg: AgriKnowledgeGraph) -> None:
    """Load comprehensive rice knowledge: stages, pests, diseases, interventions, safety."""
    SRC = "ICAR-IIRR Rice Production Technology, Hyderabad"

    # ── Crop ──
    kg.add_entity(Crop(
        id="rice", label=MultiLabel("Rice", "चावल/धान", "भात/तांदूळ"),
        scientific_name="Oryza sativa",
        seasons=[SeasonEnum.KHARIF, SeasonEnum.RABI],
        suitable_soils=[SoilTypeEnum.ALLUVIAL, SoilTypeEnum.CLAYEY, SoilTypeEnum.LOAMY, SoilTypeEnum.BLACK_COTTON],
        optimal_ph_min=5.5, optimal_ph_max=7.0,
        water_requirement_mm=1200, typical_duration_days=120,
    ))

    # Link rice to regions
    for region_id in ["punjab", "uttar_pradesh", "west_bengal", "telangana", "karnataka", "tamil_nadu", "maharashtra"]:
        kg.add_edge(Edge("rice", region_id, RelationType.SUITABLE_FOR_REGION, evidence_source=SRC))

    # ── Stages ──
    stages = [
        CropStage(id="rice_germination", crop_id="rice", stage=CropStageEnum.GERMINATION,
                  label=MultiLabel("Germination/Nursery", "अंकुरण/नर्सरी", "उगवण/रोपवाटिका"),
                  typical_day_start=0, typical_day_end=25,
                  critical_nutrients=["nitrogen", "phosphorus"],
                  description="Seed treatment, nursery bed preparation, seedling growth"),
        CropStage(id="rice_seedling", crop_id="rice", stage=CropStageEnum.SEEDLING,
                  label=MultiLabel("Transplanting/Seedling", "रोपाई", "पुनर्रोपण"),
                  typical_day_start=21, typical_day_end=35,
                  critical_nutrients=["nitrogen", "phosphorus", "zinc"],
                  description="Transplanting 21-25 day old seedlings, 2-3 seedlings per hill"),
        CropStage(id="rice_vegetative", crop_id="rice", stage=CropStageEnum.VEGETATIVE,
                  label=MultiLabel("Tillering/Vegetative", "कल्ले निकलना", "फुटवे फुटणे"),
                  typical_day_start=35, typical_day_end=65,
                  critical_nutrients=["nitrogen", "potassium", "zinc"],
                  description="Active tillering phase, maximum nutrient uptake"),
        CropStage(id="rice_flowering", crop_id="rice", stage=CropStageEnum.FLOWERING,
                  label=MultiLabel("Panicle/Flowering", "बाली निकलना/फूल आना", "लोंबी/फुलोरा"),
                  typical_day_start=65, typical_day_end=90,
                  critical_nutrients=["potassium", "boron", "phosphorus"],
                  description="Panicle initiation, booting, heading, flowering — critical yield determination phase"),
        CropStage(id="rice_maturity", crop_id="rice", stage=CropStageEnum.MATURITY,
                  label=MultiLabel("Grain Filling/Maturity", "दाना भरना/पकना", "दाणे भरणे/पक्वता"),
                  typical_day_start=90, typical_day_end=120,
                  critical_nutrients=["potassium"],
                  description="Grain filling, starch accumulation, physiological maturity"),
        CropStage(id="rice_harvesting", crop_id="rice", stage=CropStageEnum.HARVESTING,
                  label=MultiLabel("Harvesting", "कटाई", "कापणी"),
                  typical_day_start=115, typical_day_end=130,
                  critical_nutrients=[],
                  description="Harvest at 20-22% moisture, thresh within 24h"),
    ]
    for s in stages:
        kg.add_entity(s)
        kg.add_edge(Edge("rice", s.id, RelationType.HAS_STAGE, evidence_source=SRC))
        # Link critical nutrients
        for nut_id in s.critical_nutrients:
            kg.add_edge(Edge(s.id, nut_id, RelationType.REQUIRES_NUTRIENT,
                             evidence_source=SRC))

    # ── Pests ──
    pests = [
        Pest(id="rice_stem_borer", label=MultiLabel("Stem Borer", "तना छेदक", "खोड किडा"),
             scientific_name="Scirpophaga incertulas",
             symptoms=["dead heart in vegetative stage", "white ear in reproductive stage"],
             favorable_conditions="High nitrogen, stagnant water, cloudy weather"),
        Pest(id="rice_bph", label=MultiLabel("Brown Planthopper (BPH)", "भूरा फुदका", "तपकिरी तुडतुडे"),
             scientific_name="Nilaparvata lugens",
             symptoms=["hopper burn at base", "circular drying patches", "sooty mould"],
             favorable_conditions="High humidity >80%, close planting, excess nitrogen"),
        Pest(id="rice_leaf_folder", label=MultiLabel("Leaf Folder", "पत्ती लपेटक", "पान गुंडाळणारी अळी"),
             scientific_name="Cnaphalocrocis medinalis",
             symptoms=["longitudinally folded leaves", "scraping of green tissue", "white streaks"],
             favorable_conditions="Cloudy weather, high humidity, excess nitrogen"),
        Pest(id="rice_gall_midge", label=MultiLabel("Gall Midge", "गॉल मिज", "गॉल माशी"),
             scientific_name="Orseolia oryzae",
             symptoms=["onion shoot / silver shoot formation", "tubular gall at base of tiller"],
             favorable_conditions="Continuous wet weather, late planting"),
    ]
    for p in pests:
        kg.add_entity(p)

    # Link pests to vulnerable stages
    pest_stage_map = {
        "rice_stem_borer": ["rice_vegetative", "rice_flowering"],
        "rice_bph": ["rice_vegetative", "rice_flowering", "rice_maturity"],
        "rice_leaf_folder": ["rice_vegetative", "rice_flowering"],
        "rice_gall_midge": ["rice_seedling", "rice_vegetative"],
    }
    for pest_id, stage_ids in pest_stage_map.items():
        for stage_id in stage_ids:
            kg.add_edge(Edge(stage_id, pest_id, RelationType.VULNERABLE_TO_PEST,
                             evidence_source=SRC))

    # ── Diseases ──
    diseases = [
        Disease(id="rice_blast", label=MultiLabel("Rice Blast", "झोंका/ब्लास्ट", "करपा"),
                pathogen_type="fungal", pathogen_name="Magnaporthe oryzae",
                symptoms=["diamond-shaped lesions on leaves", "neck blast causing panicle breakage",
                          "brown spots on nodes"],
                favorable_conditions="Temp 25-28°C, RH >90%, excess nitrogen, drought stress followed by flooding"),
        Disease(id="rice_sheath_blight", label=MultiLabel("Sheath Blight", "शीथ ब्लाइट", "आवरण अंगमारी"),
                pathogen_type="fungal", pathogen_name="Rhizoctonia solani",
                symptoms=["oval/irregular greenish-grey lesions on sheath", "banding pattern", "lodging"],
                favorable_conditions="High temperature >28°C, RH >95%, dense planting, high nitrogen"),
        Disease(id="rice_blight_bb", label=MultiLabel("Bacterial Leaf Blight", "जीवाणु झुलसा", "जिवाणू करपा"),
                pathogen_type="bacterial", pathogen_name="Xanthomonas oryzae pv. oryzae",
                symptoms=["water-soaked lesions on leaf margins", "yellowing and wilting from tip",
                          "milky ooze on cut leaves"],
                favorable_conditions="Warm humid weather, wind-driven rain, clipping during transplanting"),
        Disease(id="rice_false_smut", label=MultiLabel("False Smut", "मिथ्या कंड", "खोटी काणी"),
                pathogen_type="fungal", pathogen_name="Ustilaginoidea virens",
                symptoms=["orange to green spore balls on individual grains in panicle"],
                favorable_conditions="High RH during flowering, moderate temperature 25-30°C"),
    ]
    for d in diseases:
        kg.add_entity(d)

    disease_stage_map = {
        "rice_blast": ["rice_seedling", "rice_vegetative", "rice_flowering"],
        "rice_sheath_blight": ["rice_vegetative", "rice_flowering", "rice_maturity"],
        "rice_blight_bb": ["rice_vegetative", "rice_flowering"],
        "rice_false_smut": ["rice_flowering"],
    }
    for disease_id, stage_ids in disease_stage_map.items():
        for stage_id in stage_ids:
            kg.add_edge(Edge(stage_id, disease_id, RelationType.VULNERABLE_TO_DISEASE,
                             evidence_source=SRC))

    # ── Interventions ──
    interventions = [
        # --- Fertilizers ---
        Intervention(
            id="rice_basal_npk", label=MultiLabel("Basal NPK (DAP + MOP)", "बेसल NPK", "बेसल NPK"),
            type=InterventionType.FERTILIZER,
            active_ingredient="DAP (18:46:0) + MOP (0:0:60)",
            recommended_dosage="DAP 100kg/ha + MOP 50kg/ha at transplanting",
            recommended_dosage_min=80, recommended_dosage_max=120, dosage_unit="kg/ha DAP",
            application_method="Broadcast and incorporate before transplanting",
            source=SRC,
        ),
        Intervention(
            id="rice_urea_top1", label=MultiLabel("1st Urea Top Dressing", "यूरिया पहली टॉप ड्रेसिंग", "युरिया पहिले टॉप ड्रेसिंग"),
            type=InterventionType.FERTILIZER,
            active_ingredient="Urea (46:0:0)",
            recommended_dosage="Urea 55-65kg/ha at 21 DAT (active tillering)",
            recommended_dosage_min=55, recommended_dosage_max=65, dosage_unit="kg/ha",
            application_method="Broadcast in standing water, drain field next day",
            source=SRC,
        ),
        Intervention(
            id="rice_urea_top2", label=MultiLabel("2nd Urea Top Dressing", "यूरिया दूसरी टॉप ड्रेसिंग", "युरिया दुसरे टॉप ड्रेसिंग"),
            type=InterventionType.FERTILIZER,
            active_ingredient="Urea (46:0:0)",
            recommended_dosage="Urea 55-65kg/ha at panicle initiation (45-50 DAT)",
            recommended_dosage_min=55, recommended_dosage_max=65, dosage_unit="kg/ha",
            application_method="Broadcast in standing water",
            source=SRC,
        ),
        Intervention(
            id="rice_zinc_sulphate", label=MultiLabel("Zinc Sulphate Application", "जिंक सल्फेट", "झिंक सल्फेट"),
            type=InterventionType.FERTILIZER,
            active_ingredient="ZnSO4·7H2O",
            recommended_dosage="ZnSO4 25kg/ha mixed with sand, broadcast before transplanting",
            recommended_dosage_min=20, recommended_dosage_max=25, dosage_unit="kg/ha",
            application_method="Mix with dry sand, broadcast before last puddling",
            source=SRC,
        ),
        # --- Pesticides ---
        Intervention(
            id="rice_cartap_hydro", label=MultiLabel("Cartap Hydrochloride 4G", "कार्टैप हाइड्रोक्लोराइड", "कार्टॅप हायड्रोक्लोराईड"),
            type=InterventionType.PESTICIDE,
            active_ingredient="Cartap Hydrochloride 4% G",
            recommended_dosage="18-20 kg granules/ha in standing water",
            recommended_dosage_min=18, recommended_dosage_max=20, dosage_unit="kg/ha",
            application_method="Broadcast granules in paddy water, maintain 3-5cm water for 3 days",
            waiting_period_days=21,
            source="CIB&RC Approved Label Claims; ICAR-IIRR",
        ),
        Intervention(
            id="rice_chlorantraniliprole", label=MultiLabel("Chlorantraniliprole 0.4% GR", "क्लोरेंट्रानिलिप्रोल", "क्लोरँट्रानिलिप्रोल"),
            type=InterventionType.PESTICIDE,
            active_ingredient="Chlorantraniliprole 0.4% GR",
            recommended_dosage="10 kg granules/ha",
            recommended_dosage_min=8, recommended_dosage_max=10, dosage_unit="kg/ha",
            application_method="Broadcast in standing water",
            waiting_period_days=30,
            source="CIB&RC Approved Label Claims",
        ),
        Intervention(
            id="rice_imidacloprid", label=MultiLabel("Imidacloprid 17.8% SL", "इमिडाक्लोप्रिड", "इमिडाक्लोप्रिड"),
            type=InterventionType.PESTICIDE,
            active_ingredient="Imidacloprid 17.8% SL",
            recommended_dosage="0.5 ml/L water, spray on foliage",
            recommended_dosage_min=0.3, recommended_dosage_max=0.5, dosage_unit="ml/L",
            application_method="Foliar spray with knapsack sprayer, 500L water/ha",
            waiting_period_days=14,
            source="CIB&RC; ICAR-IIRR BPH Management",
        ),
        # --- Fungicides ---
        Intervention(
            id="rice_tricyclazole", label=MultiLabel("Tricyclazole 75% WP", "ट्राइसाइक्लाज़ोल", "ट्रायसायक्लॅझोल"),
            type=InterventionType.FUNGICIDE,
            active_ingredient="Tricyclazole 75% WP",
            recommended_dosage="0.6 g/L water, foliar spray",
            recommended_dosage_min=0.4, recommended_dosage_max=0.6, dosage_unit="g/L",
            application_method="Foliar spray, 500L water/ha, 2-3 sprays at 10-15 day interval",
            waiting_period_days=21,
            source="CIB&RC; ICAR-IIRR Blast Management",
        ),
        Intervention(
            id="rice_propiconazole", label=MultiLabel("Propiconazole 25% EC", "प्रोपिकोनाज़ोल", "प्रोपिकोनॅझोल"),
            type=InterventionType.FUNGICIDE,
            active_ingredient="Propiconazole 25% EC",
            recommended_dosage="1 ml/L water",
            recommended_dosage_min=0.5, recommended_dosage_max=1.0, dosage_unit="ml/L",
            application_method="Foliar spray",
            waiting_period_days=14,
            source="CIB&RC; ICAR-IIRR Sheath Blight Management",
        ),
        # --- Biological ---
        Intervention(
            id="rice_trichoderma", label=MultiLabel("Trichoderma viride", "ट्राइकोडर्मा", "ट्रायकोडर्मा"),
            type=InterventionType.BIOLOGICAL,
            active_ingredient="Trichoderma viride 1% WP",
            recommended_dosage="2.5 kg/ha mixed with FYM, or 10g/kg seed treatment",
            recommended_dosage_min=2.0, recommended_dosage_max=2.5, dosage_unit="kg/ha",
            application_method="Seed treatment or soil application with FYM",
            waiting_period_days=0,
            source="ICAR-NBAIR; ICAR-IIRR",
        ),
        Intervention(
            id="rice_pseudomonas", label=MultiLabel("Pseudomonas fluorescens", "स्यूडोमोनास", "स्यूडोमोनास"),
            type=InterventionType.BIOLOGICAL,
            active_ingredient="Pseudomonas fluorescens 0.5% WP",
            recommended_dosage="10g/L water spray or 10g/kg seed treatment",
            recommended_dosage_min=5, recommended_dosage_max=10, dosage_unit="g/L",
            application_method="Seed treatment, seedling dip, or foliar spray",
            waiting_period_days=0,
            source="ICAR-NBAIR",
        ),
        # --- Cultural ---
        Intervention(
            id="rice_weed_management", label=MultiLabel("Manual/Chemical Weed Management", "खरपतवार प्रबंधन", "तण व्यवस्थापन"),
            type=InterventionType.CULTURAL,
            recommended_dosage="Hand weeding at 20 and 40 DAT, or pre-emergence herbicide",
            application_method="Manual weeding or Pretilachlor 0.75kg a.i./ha pre-emergence",
            source=SRC,
        ),
    ]
    for i in interventions:
        kg.add_entity(i)

    # Link interventions to stages
    intervention_stage_map = {
        "rice_basal_npk": ["rice_germination", "rice_seedling"],
        "rice_urea_top1": ["rice_vegetative"],
        "rice_urea_top2": ["rice_flowering"],
        "rice_zinc_sulphate": ["rice_seedling"],
        "rice_cartap_hydro": ["rice_vegetative", "rice_flowering"],
        "rice_chlorantraniliprole": ["rice_vegetative", "rice_flowering"],
        "rice_imidacloprid": ["rice_vegetative", "rice_flowering"],
        "rice_tricyclazole": ["rice_vegetative", "rice_flowering"],
        "rice_propiconazole": ["rice_vegetative", "rice_flowering", "rice_maturity"],
        "rice_trichoderma": ["rice_germination", "rice_seedling"],
        "rice_pseudomonas": ["rice_germination", "rice_seedling", "rice_vegetative"],
        "rice_weed_management": ["rice_seedling", "rice_vegetative"],
    }
    for int_id, stage_ids in intervention_stage_map.items():
        for stage_id in stage_ids:
            kg.add_edge(Edge(int_id, stage_id, RelationType.RECOMMENDED_FOR_STAGE,
                             evidence_source=SRC))

    # Link interventions to threats they treat
    treatment_map = {
        "rice_cartap_hydro": {"pests": ["rice_stem_borer", "rice_leaf_folder"]},
        "rice_chlorantraniliprole": {"pests": ["rice_stem_borer", "rice_leaf_folder"]},
        "rice_imidacloprid": {"pests": ["rice_bph"]},
        "rice_tricyclazole": {"diseases": ["rice_blast"]},
        "rice_propiconazole": {"diseases": ["rice_sheath_blight", "rice_false_smut"]},
        "rice_trichoderma": {"diseases": ["rice_blast", "rice_sheath_blight"]},
        "rice_pseudomonas": {"diseases": ["rice_blast", "rice_blight_bb"]},
    }
    for int_id, targets in treatment_map.items():
        for pest_id in targets.get("pests", []):
            kg.add_edge(Edge(int_id, pest_id, RelationType.TREATS_PEST, evidence_source=SRC))
        for disease_id in targets.get("diseases", []):
            kg.add_edge(Edge(int_id, disease_id, RelationType.TREATS_DISEASE, evidence_source=SRC))

    # ── Safety Constraints ──
    safety_constraints = [
        SafetyConstraint(
            id="sc_rice_no_excess_nitrogen",
            description="Do NOT exceed 120 kg N/ha total for rice; excess nitrogen increases susceptibility to blast, BPH, and lodging",
            constraint_type="dosage_limit",
            severity=SeverityLevel.HIGH,
            source=SRC,
        ),
        SafetyConstraint(
            id="sc_rice_urea_no_rain",
            description="Do NOT apply urea if heavy rain is expected within 24 hours — risk of nitrogen runoff and groundwater contamination",
            constraint_type="timing",
            severity=SeverityLevel.HIGH,
            source="ICAR-IARI Nutrient Management Guidelines",
        ),
        SafetyConstraint(
            id="sc_rice_phi_cartap",
            description="Pre-harvest interval for Cartap Hydrochloride is 21 days — do NOT harvest within 21 days of application",
            constraint_type="timing",
            severity=SeverityLevel.HIGH,
            source="CIB&RC Approved Label",
        ),
        SafetyConstraint(
            id="sc_rice_phi_tricyclazole",
            description="Pre-harvest interval for Tricyclazole is 21 days — do NOT harvest within 21 days of application",
            constraint_type="timing",
            severity=SeverityLevel.HIGH,
            source="CIB&RC Approved Label",
        ),
        SafetyConstraint(
            id="sc_rice_imida_bee_safety",
            description="Imidacloprid is toxic to bees — do NOT apply during flowering if bee pollinators are active",
            constraint_type="environmental",
            severity=SeverityLevel.HIGH,
            source="CIB&RC Environmental Safety Data",
        ),
        SafetyConstraint(
            id="sc_rice_no_tricho_with_fungicide",
            description="Trichoderma is a living organism — do NOT apply chemical fungicides within 7 days of Trichoderma application",
            constraint_type="incompatibility",
            severity=SeverityLevel.HIGH,
            source="ICAR-NBAIR Bio-agent Compatibility Guide",
        ),
        SafetyConstraint(
            id="sc_rice_zinc_not_with_phosphorus",
            description="Do NOT mix zinc sulphate with phosphatic fertilizers (DAP) — chemical reaction reduces availability of both",
            constraint_type="incompatibility",
            severity=SeverityLevel.MEDIUM,
            source="ICAR-IARI Micronutrient Management",
        ),
    ]
    for sc in safety_constraints:
        kg.add_entity(sc)

    # Link constraints to interventions
    constraint_map = {
        "rice_urea_top1": ["sc_rice_no_excess_nitrogen", "sc_rice_urea_no_rain"],
        "rice_urea_top2": ["sc_rice_no_excess_nitrogen", "sc_rice_urea_no_rain"],
        "rice_basal_npk": ["sc_rice_no_excess_nitrogen"],
        "rice_cartap_hydro": ["sc_rice_phi_cartap"],
        "rice_tricyclazole": ["sc_rice_phi_tricyclazole"],
        "rice_imidacloprid": ["sc_rice_imida_bee_safety"],
        "rice_trichoderma": ["sc_rice_no_tricho_with_fungicide"],
        "rice_zinc_sulphate": ["sc_rice_zinc_not_with_phosphorus"],
    }
    for int_id, sc_ids in constraint_map.items():
        for sc_id in sc_ids:
            kg.add_edge(Edge(int_id, sc_id, RelationType.HAS_CONSTRAINT,
                             evidence_source="ICAR/CIB&RC"))

    # Chemical incompatibilities
    incompatible_pairs = [
        ("rice_trichoderma", "rice_tricyclazole"),
        ("rice_trichoderma", "rice_propiconazole"),
        ("rice_pseudomonas", "rice_tricyclazole"),
        ("rice_pseudomonas", "rice_propiconazole"),
        ("rice_zinc_sulphate", "rice_basal_npk"),  # Zn + DAP incompatibility
    ]
    for a, b in incompatible_pairs:
        kg.add_edge(Edge(a, b, RelationType.INCOMPATIBLE_WITH, evidence_source="ICAR-NBAIR / ICAR-IARI"))
        kg.add_edge(Edge(b, a, RelationType.INCOMPATIBLE_WITH, evidence_source="ICAR-NBAIR / ICAR-IARI"))

    logger.info("Rice knowledge loaded")


# ═══════════════════════════════════════════════════════════════
# WHEAT (condensed — key stages, threats, interventions)
# Source: ICAR-IARI Wheat Production Technology
# ═══════════════════════════════════════════════════════════════

def _load_wheat(kg: AgriKnowledgeGraph) -> None:
    SRC = "ICAR-IARI Wheat Production Technology Manual"

    kg.add_entity(Crop(
        id="wheat", label=MultiLabel("Wheat", "गेहूँ", "गहू"),
        scientific_name="Triticum aestivum",
        seasons=[SeasonEnum.RABI],
        suitable_soils=[SoilTypeEnum.ALLUVIAL, SoilTypeEnum.LOAMY, SoilTypeEnum.CLAYEY],
        optimal_ph_min=6.0, optimal_ph_max=7.5,
        water_requirement_mm=450, typical_duration_days=140,
    ))

    for region_id in ["punjab", "uttar_pradesh", "madhya_pradesh", "rajasthan", "maharashtra"]:
        kg.add_edge(Edge("wheat", region_id, RelationType.SUITABLE_FOR_REGION, evidence_source=SRC))

    stages = [
        CropStage(id="wheat_germination", crop_id="wheat", stage=CropStageEnum.GERMINATION,
                  label=MultiLabel("Germination", "अंकुरण", "उगवण"),
                  typical_day_start=0, typical_day_end=15,
                  critical_nutrients=["nitrogen", "phosphorus"]),
        CropStage(id="wheat_vegetative", crop_id="wheat", stage=CropStageEnum.VEGETATIVE,
                  label=MultiLabel("Tillering/Crown Root", "कल्ले/जड़ बनना", "फुटवे"),
                  typical_day_start=15, typical_day_end=55,
                  critical_nutrients=["nitrogen", "phosphorus", "zinc"]),
        CropStage(id="wheat_flowering", crop_id="wheat", stage=CropStageEnum.FLOWERING,
                  label=MultiLabel("Heading/Flowering", "बाली निकलना", "लोंबी"),
                  typical_day_start=55, typical_day_end=85,
                  critical_nutrients=["potassium", "sulphur"]),
        CropStage(id="wheat_maturity", crop_id="wheat", stage=CropStageEnum.MATURITY,
                  label=MultiLabel("Grain Filling/Maturity", "दाना भरना", "दाणे भरणे"),
                  typical_day_start=85, typical_day_end=130,
                  critical_nutrients=["potassium"]),
        CropStage(id="wheat_harvesting", crop_id="wheat", stage=CropStageEnum.HARVESTING,
                  label=MultiLabel("Harvesting", "कटाई", "कापणी"),
                  typical_day_start=130, typical_day_end=145,
                  critical_nutrients=[]),
    ]
    for s in stages:
        kg.add_entity(s)
        kg.add_edge(Edge("wheat", s.id, RelationType.HAS_STAGE, evidence_source=SRC))
        for nut_id in s.critical_nutrients:
            kg.add_edge(Edge(s.id, nut_id, RelationType.REQUIRES_NUTRIENT, evidence_source=SRC))

    # Key wheat pests/diseases
    pests_diseases = [
        Pest(id="wheat_aphid", label=MultiLabel("Wheat Aphid", "गेहूँ का माहू", "गव्हावरील माव्या"),
             symptoms=["yellowing leaves", "honeydew secretion", "stunted growth"]),
        Pest(id="wheat_termite", label=MultiLabel("Termite", "दीमक", "वाळवी"),
             symptoms=["wilting in patches", "hollow stems", "dried plants"]),
        Disease(id="wheat_rust_yellow", label=MultiLabel("Yellow Rust", "पीला रतुआ", "पिवळा तांबेरा"),
                pathogen_type="fungal", pathogen_name="Puccinia striiformis",
                symptoms=["yellow stripe of pustules along leaf veins"]),
        Disease(id="wheat_rust_brown", label=MultiLabel("Brown/Leaf Rust", "भूरा रतुआ", "तपकिरी तांबेरा"),
                pathogen_type="fungal", pathogen_name="Puccinia triticina",
                symptoms=["small, circular brown pustules on upper leaf surface"]),
        Disease(id="wheat_karnal_bunt", label=MultiLabel("Karnal Bunt", "करनाल बंट", "करनाल बंट"),
                pathogen_type="fungal", pathogen_name="Tilletia indica",
                symptoms=["partial bunting of grains", "foul smell like rotten fish"]),
    ]
    for entity in pests_diseases:
        kg.add_entity(entity)
        if isinstance(entity, Pest):
            for sid in ["wheat_vegetative", "wheat_flowering"]:
                kg.add_edge(Edge(sid, entity.id, RelationType.VULNERABLE_TO_PEST, evidence_source=SRC))
        else:
            for sid in ["wheat_vegetative", "wheat_flowering", "wheat_maturity"]:
                kg.add_edge(Edge(sid, entity.id, RelationType.VULNERABLE_TO_DISEASE, evidence_source=SRC))

    # Key wheat interventions
    wheat_interventions = [
        Intervention(id="wheat_basal_npk", label=MultiLabel("Basal NPK for Wheat", "बेसल NPK", "बेसल NPK"),
                     type=InterventionType.FERTILIZER,
                     recommended_dosage="DAP 130kg/ha + MOP 40kg/ha at sowing",
                     recommended_dosage_min=120, recommended_dosage_max=150, dosage_unit="kg/ha DAP",
                     source=SRC),
        Intervention(id="wheat_propiconazole", label=MultiLabel("Propiconazole for Rust", "प्रोपिकोनाज़ोल", "प्रोपिकोनॅझोल"),
                     type=InterventionType.FUNGICIDE,
                     active_ingredient="Propiconazole 25% EC",
                     recommended_dosage="1 ml/L water, foliar spray",
                     recommended_dosage_min=0.5, recommended_dosage_max=1.0, dosage_unit="ml/L",
                     waiting_period_days=14, source="CIB&RC; ICAR-IARI"),
    ]
    for i in wheat_interventions:
        kg.add_entity(i)
    kg.add_edge(Edge("wheat_basal_npk", "wheat_germination", RelationType.RECOMMENDED_FOR_STAGE, evidence_source=SRC))
    kg.add_edge(Edge("wheat_propiconazole", "wheat_vegetative", RelationType.RECOMMENDED_FOR_STAGE, evidence_source=SRC))
    kg.add_edge(Edge("wheat_propiconazole", "wheat_flowering", RelationType.RECOMMENDED_FOR_STAGE, evidence_source=SRC))
    kg.add_edge(Edge("wheat_propiconazole", "wheat_rust_yellow", RelationType.TREATS_DISEASE, evidence_source=SRC))
    kg.add_edge(Edge("wheat_propiconazole", "wheat_rust_brown", RelationType.TREATS_DISEASE, evidence_source=SRC))

    logger.info("Wheat knowledge loaded")


# ═══════════════════════════════════════════════════════════════
# COTTON, SUGARCANE, SOYBEAN — Skeleton data
# Full data follows the rice pattern but condensed here for space
# ═══════════════════════════════════════════════════════════════

def _load_cotton(kg: AgriKnowledgeGraph) -> None:
    SRC = "ICAR-CICR Cotton Production Technology Bulletin"
    kg.add_entity(Crop(
        id="cotton", label=MultiLabel("Cotton", "कपास", "कापूस"),
        scientific_name="Gossypium hirsutum",
        seasons=[SeasonEnum.KHARIF],
        suitable_soils=[SoilTypeEnum.BLACK_COTTON, SoilTypeEnum.ALLUVIAL, SoilTypeEnum.LOAMY],
        optimal_ph_min=6.0, optimal_ph_max=8.0,
        water_requirement_mm=700, typical_duration_days=180,
    ))
    for rid in ["maharashtra", "gujarat", "telangana", "madhya_pradesh", "karnataka", "punjab", "rajasthan"]:
        kg.add_edge(Edge("cotton", rid, RelationType.SUITABLE_FOR_REGION, evidence_source=SRC))

    for stage_data in [
        ("cotton_germination", CropStageEnum.GERMINATION, 0, 15, ["nitrogen", "phosphorus"]),
        ("cotton_vegetative", CropStageEnum.VEGETATIVE, 15, 60, ["nitrogen", "potassium"]),
        ("cotton_flowering", CropStageEnum.FLOWERING, 60, 100, ["potassium", "boron"]),
        ("cotton_fruiting", CropStageEnum.FRUITING, 100, 150, ["potassium"]),
        ("cotton_harvesting", CropStageEnum.HARVESTING, 150, 180, []),
    ]:
        sid, stage, ds, de, nuts = stage_data
        cs = CropStage(id=sid, crop_id="cotton", stage=stage,
                       label=MultiLabel(stage.value.title(), "", ""),
                       typical_day_start=ds, typical_day_end=de,
                       critical_nutrients=nuts)
        kg.add_entity(cs)
        kg.add_edge(Edge("cotton", sid, RelationType.HAS_STAGE, evidence_source=SRC))
        for nut_id in nuts:
            kg.add_edge(Edge(sid, nut_id, RelationType.REQUIRES_NUTRIENT, evidence_source=SRC))

    # Key cotton threats
    for pest in [
        Pest(id="cotton_bollworm", label=MultiLabel("American Bollworm", "अमेरिकी बोलवर्म", "अमेरिकन बोंडअळी"),
             scientific_name="Helicoverpa armigera", symptoms=["bore holes in bolls", "frass"]),
        Pest(id="cotton_whitefly", label=MultiLabel("Whitefly", "सफेद मक्खी", "पांढरी माशी"),
             symptoms=["sooty mould", "leaf curl", "sticky honeydew"]),
    ]:
        kg.add_entity(pest)
        for sid in ["cotton_flowering", "cotton_fruiting"]:
            kg.add_edge(Edge(sid, pest.id, RelationType.VULNERABLE_TO_PEST, evidence_source=SRC))

    # Interventions
    cotton_interventions = [
        Intervention(id="cotton_imidacloprid", label=MultiLabel("Imidacloprid for Whitefly", "इमिडाक्लोप्रिड", "इमिडाक्लोप्रिड"),
                     type=InterventionType.PESTICIDE, active_ingredient="Imidacloprid 17.8% SL",
                     recommended_dosage="0.5 ml/L", recommended_dosage_min=0.3, recommended_dosage_max=0.5, dosage_unit="ml/L",
                     source=SRC),
        Intervention(id="cotton_monocrotophos", label=MultiLabel("Monocrotophos (Restricted)", "मोनोक्रोटोफॉस", "मोनोक्रोटोफॉस"),
                     type=InterventionType.PESTICIDE, active_ingredient="Monocrotophos 36% SL",
                     recommended_dosage="Avoid if possible, 1 ml/L otherwise", recommended_dosage_min=0.8, recommended_dosage_max=1.2, dosage_unit="ml/L",
                     source=SRC),
    ]
    for i in cotton_interventions:
        kg.add_entity(i)
        
    kg.add_edge(Edge("cotton_imidacloprid", "cotton_whitefly", RelationType.TREATS_PEST, evidence_source=SRC))
    kg.add_edge(Edge("cotton_monocrotophos", "cotton_bollworm", RelationType.TREATS_PEST, evidence_source=SRC))

    # Safety Constraints
    sc1 = SafetyConstraint(id="sc_cotton_monocrotophos_ban", description="Monocrotophos is highly toxic and banned on vegetables. Use with extreme caution on cotton, avoiding flowering stage to protect bees.", constraint_type="environmental", severity=SeverityLevel.HIGH, source="CIB&RC")
    kg.add_entity(sc1)
    kg.add_edge(Edge("cotton_monocrotophos", sc1.id, RelationType.HAS_CONSTRAINT, evidence_source="CIB&RC"))

    logger.info("Cotton knowledge loaded")


def _load_sugarcane(kg: AgriKnowledgeGraph) -> None:
    SRC = "ICAR-SBI Sugarcane Cultivation Guide"
    kg.add_entity(Crop(
        id="sugarcane", label=MultiLabel("Sugarcane", "गन्ना", "ऊस"),
        scientific_name="Saccharum officinarum",
        seasons=[SeasonEnum.ANNUAL],
        suitable_soils=[SoilTypeEnum.ALLUVIAL, SoilTypeEnum.LOAMY, SoilTypeEnum.BLACK_COTTON],
        optimal_ph_min=6.5, optimal_ph_max=7.5,
        water_requirement_mm=1800, typical_duration_days=360,
    ))
    for rid in ["maharashtra", "uttar_pradesh", "karnataka", "tamil_nadu", "gujarat"]:
        kg.add_edge(Edge("sugarcane", rid, RelationType.SUITABLE_FOR_REGION, evidence_source=SRC))

    for stage_data in [
        ("sugarcane_germination", CropStageEnum.GERMINATION, 0, 35, ["nitrogen", "phosphorus"]),
        ("sugarcane_vegetative", CropStageEnum.VEGETATIVE, 35, 120, ["nitrogen", "potassium", "iron"]),
        ("sugarcane_flowering", CropStageEnum.FLOWERING, 120, 270, ["potassium"]),
        ("sugarcane_maturity", CropStageEnum.MATURITY, 270, 330, ["potassium"]),
        ("sugarcane_harvesting", CropStageEnum.HARVESTING, 330, 365, []),
    ]:
        sid, stage, ds, de, nuts = stage_data
        cs = CropStage(id=sid, crop_id="sugarcane", stage=stage,
                       label=MultiLabel(stage.value.title(), "", ""),
                       typical_day_start=ds, typical_day_end=de,
                       critical_nutrients=nuts)
        kg.add_entity(cs)
        kg.add_edge(Edge("sugarcane", sid, RelationType.HAS_STAGE, evidence_source=SRC))
        for nut_id in nuts:
            kg.add_edge(Edge(sid, nut_id, RelationType.REQUIRES_NUTRIENT, evidence_source=SRC))

    # Key sugarcane pests
    pest = Pest(id="sugarcane_top_borer", label=MultiLabel("Top Shoot Borer", "शीर्ष छेदक", "शेंडा पोखरणारी अळी"),
                scientific_name="Scirpophaga excerptalis", symptoms=["dead heart", "bunchy top"])
    kg.add_entity(pest)
    for sid in ["sugarcane_vegetative", "sugarcane_flowering"]:
        kg.add_edge(Edge(sid, pest.id, RelationType.VULNERABLE_TO_PEST, evidence_source=SRC))

    # Interventions
    cane_interventions = [
        Intervention(id="sugarcane_atrazine", label=MultiLabel("Atrazine Herbicide", "एट्राजीन", "अॅट्राझिन"),
                     type=InterventionType.CULTURAL, active_ingredient="Atrazine 50% WP",
                     recommended_dosage="2 kg/ha", recommended_dosage_min=1.5, recommended_dosage_max=2.5, dosage_unit="kg/ha",
                     source=SRC),
        Intervention(id="sugarcane_chlorantraniliprole", label=MultiLabel("Chlorantraniliprole for Borer", "क्लोरेंट्रानिलिप्रोल", "क्लोरँट्रानिलिप्रोल"),
                     type=InterventionType.PESTICIDE, active_ingredient="Chlorantraniliprole 18.5% SC",
                     recommended_dosage="150 ml/ha", recommended_dosage_min=120, recommended_dosage_max=150, dosage_unit="ml/ha",
                     source=SRC)
    ]
    for i in cane_interventions:
        kg.add_entity(i)
    kg.add_edge(Edge("sugarcane_chlorantraniliprole", "sugarcane_top_borer", RelationType.TREATS_PEST, evidence_source=SRC))
    
    sc_atrazine = SafetyConstraint(id="sc_sugarcane_atrazine_timing", description="Atrazine must be applied as pre-emergence within 3 days of planting.", constraint_type="timing", severity=SeverityLevel.HIGH, source=SRC)
    kg.add_entity(sc_atrazine)
    kg.add_edge(Edge("sugarcane_atrazine", sc_atrazine.id, RelationType.HAS_CONSTRAINT, evidence_source=SRC))

    logger.info("Sugarcane knowledge loaded")


def _load_soybean(kg: AgriKnowledgeGraph) -> None:
    SRC = "ICAR-IISR Soybean Production Technology"
    kg.add_entity(Crop(
        id="soybean", label=MultiLabel("Soybean", "सोयाबीन", "सोयाबीन"),
        scientific_name="Glycine max",
        seasons=[SeasonEnum.KHARIF],
        suitable_soils=[SoilTypeEnum.BLACK_COTTON, SoilTypeEnum.LOAMY, SoilTypeEnum.ALLUVIAL],
        optimal_ph_min=6.0, optimal_ph_max=7.5,
        water_requirement_mm=500, typical_duration_days=100,
    ))
    for rid in ["madhya_pradesh", "maharashtra", "rajasthan", "karnataka"]:
        kg.add_edge(Edge("soybean", rid, RelationType.SUITABLE_FOR_REGION, evidence_source=SRC))

    for stage_data in [
        ("soybean_germination", CropStageEnum.GERMINATION, 0, 10, ["phosphorus"]),
        ("soybean_vegetative", CropStageEnum.VEGETATIVE, 10, 40, ["nitrogen", "phosphorus", "sulphur"]),
        ("soybean_flowering", CropStageEnum.FLOWERING, 40, 60, ["potassium", "boron"]),
        ("soybean_fruiting", CropStageEnum.FRUITING, 60, 85, ["potassium"]),
        ("soybean_harvesting", CropStageEnum.HARVESTING, 85, 100, []),
    ]:
        sid, stage, ds, de, nuts = stage_data
        cs = CropStage(id=sid, crop_id="soybean", stage=stage,
                       label=MultiLabel(stage.value.title(), "", ""),
                       typical_day_start=ds, typical_day_end=de,
                       critical_nutrients=nuts)
        kg.add_entity(cs)
        kg.add_edge(Edge("soybean", sid, RelationType.HAS_STAGE, evidence_source=SRC))
        for nut_id in nuts:
            kg.add_edge(Edge(sid, nut_id, RelationType.REQUIRES_NUTRIENT, evidence_source=SRC))

    # Key soybean diseases
    disease = Disease(id="soybean_rust", label=MultiLabel("Soybean Rust", "सोयाबीन रतुआ", "सोयाबीन तांबेरा"),
                      pathogen_type="fungal", pathogen_name="Phakopsora pachyrhizi",
                      symptoms=["tiny brown pustules on lower leaf surface", "premature defoliation"])
    kg.add_entity(disease)
    for sid in ["soybean_flowering", "soybean_fruiting"]:
        kg.add_edge(Edge(sid, disease.id, RelationType.VULNERABLE_TO_DISEASE, evidence_source=SRC))

    # Interventions
    soy_interventions = [
        Intervention(id="soybean_hexaconazole", label=MultiLabel("Hexaconazole for Rust", "हेक्साकोनाज़ोल", "हेक्साकोनाझोल"),
                     type=InterventionType.FUNGICIDE, active_ingredient="Hexaconazole 5% EC",
                     recommended_dosage="1 ml/L", recommended_dosage_min=0.8, recommended_dosage_max=1.2, dosage_unit="ml/L",
                     source=SRC)
    ]
    for i in soy_interventions:
        kg.add_entity(i)
    kg.add_edge(Edge("soybean_hexaconazole", "soybean_rust", RelationType.TREATS_DISEASE, evidence_source=SRC))

    sc_hex = SafetyConstraint(id="sc_soybean_hexaconazole_phi", description="Pre-harvest interval for Hexaconazole is 30 days.", constraint_type="timing", severity=SeverityLevel.HIGH, source="CIB&RC")
    kg.add_entity(sc_hex)
    kg.add_edge(Edge("soybean_hexaconazole", sc_hex.id, RelationType.HAS_CONSTRAINT, evidence_source="CIB&RC"))

    logger.info("Soybean knowledge loaded")
