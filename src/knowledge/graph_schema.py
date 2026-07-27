"""
CADI Knowledge Graph — Ontology Schema

Defines the entity types, relationship types, and constraint types
that form the agricultural knowledge graph. This is the "data model"
for all agronomic knowledge in the system.

Design principles:
  - Causal edges: relationships encode causal directionality, not just
    taxonomic membership. `Intervention --treats--> Disease` means
    "applying this intervention causally reduces disease severity."
  - Temporal versioning: entities like GovtScheme carry validity windows.
  - Safety-first: every Intervention has mandatory SafetyConstraints.
  - Multilingual: all labels carry en/hi/mr translations.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

class CropStageEnum(str, enum.Enum):
    """Phenological stages common across major Indian crops."""
    GERMINATION   = "germination"
    SEEDLING      = "seedling"
    VEGETATIVE    = "vegetative"
    FLOWERING     = "flowering"
    FRUITING      = "fruiting"
    MATURITY      = "maturity"
    HARVESTING    = "harvesting"
    POST_HARVEST  = "post_harvest"


class InterventionType(str, enum.Enum):
    """Categories of farm interventions."""
    FERTILIZER    = "fertilizer"
    PESTICIDE     = "pesticide"
    FUNGICIDE     = "fungicide"
    HERBICIDE     = "herbicide"
    IRRIGATION    = "irrigation"
    CULTURAL      = "cultural"       # e.g. weeding, mulching, pruning
    BIOLOGICAL    = "biological"     # bio-agents like Trichoderma
    MECHANICAL    = "mechanical"     # traps, nets


class SeverityLevel(str, enum.Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class SoilTypeEnum(str, enum.Enum):
    ALLUVIAL     = "alluvial"
    BLACK_COTTON = "black_cotton"
    RED          = "red"
    LATERITE     = "laterite"
    SANDY        = "sandy"
    CLAYEY       = "clayey"
    LOAMY        = "loamy"
    SALINE       = "saline"


class SeasonEnum(str, enum.Enum):
    KHARIF = "kharif"       # monsoon: June–Oct
    RABI   = "rabi"         # winter: Oct–March
    ZAID   = "zaid"         # summer: March–June
    ANNUAL = "annual"       # year-round


# ─────────────────────────────────────────────────────────────
# Multilingual Label
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MultiLabel:
    """Trilingual label for display purposes."""
    en: str
    hi: str = ""
    mr: str = ""

    def get(self, lang: str = "en") -> str:
        return getattr(self, lang, "") or self.en


# ─────────────────────────────────────────────────────────────
# Entity Nodes
# ─────────────────────────────────────────────────────────────

@dataclass
class Crop:
    """A cultivated crop species."""
    id: str                                     # e.g. "rice", "wheat"
    label: MultiLabel
    scientific_name: str = ""
    seasons: list[SeasonEnum] = field(default_factory=list)
    suitable_soils: list[SoilTypeEnum] = field(default_factory=list)
    optimal_ph_min: float = 0.0
    optimal_ph_max: float = 14.0
    water_requirement_mm: float = 0.0           # seasonal total
    typical_duration_days: int = 0              # seed to harvest


@dataclass
class CropStage:
    """A phenological stage within a crop's lifecycle."""
    id: str                                     # e.g. "rice_flowering"
    crop_id: str
    stage: CropStageEnum
    label: MultiLabel
    typical_day_start: int = 0                  # days after sowing
    typical_day_end: int = 0
    critical_nutrients: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class Nutrient:
    """A macro- or micro-nutrient required by crops."""
    id: str                                     # e.g. "nitrogen", "zinc"
    label: MultiLabel
    symbol: str = ""                            # e.g. "N", "Zn"
    category: str = ""                          # "macro" | "micro"


@dataclass
class Pest:
    """An insect pest or animal pest."""
    id: str
    label: MultiLabel
    scientific_name: str = ""
    symptoms: list[str] = field(default_factory=list)
    favorable_conditions: str = ""              # e.g. "high humidity, 25-30°C"


@dataclass
class Disease:
    """A crop disease (fungal, bacterial, viral)."""
    id: str
    label: MultiLabel
    pathogen_type: str = ""                     # "fungal"|"bacterial"|"viral"
    pathogen_name: str = ""
    symptoms: list[str] = field(default_factory=list)
    favorable_conditions: str = ""


@dataclass
class Intervention:
    """A specific management action a farmer can take."""
    id: str
    label: MultiLabel
    type: InterventionType
    active_ingredient: str = ""                 # for chemicals
    recommended_dosage: str = ""                # e.g. "2ml/L water"
    recommended_dosage_min: float = 0.0         # numeric lower bound
    recommended_dosage_max: float = 0.0         # numeric upper bound
    dosage_unit: str = ""                       # e.g. "ml/L", "kg/ha"
    application_method: str = ""                # e.g. "foliar spray"
    waiting_period_days: int = 0                # pre-harvest interval
    source: str = ""                            # ICAR/KVK reference
    source_url: str = ""


@dataclass
class SafetyConstraint:
    """A hard safety rule that must never be violated."""
    id: str
    description: str
    constraint_type: str                        # "dosage_limit"|"incompatibility"|"timing"|"stage_restriction"|"environmental"
    severity: SeverityLevel = SeverityLevel.HIGH
    source: str = ""                            # ICAR/KVK reference


@dataclass
class GovtScheme:
    """A government agricultural scheme or subsidy."""
    id: str
    label: MultiLabel
    description: str = ""
    eligible_crops: list[str] = field(default_factory=list)
    eligible_regions: list[str] = field(default_factory=list)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    url: str = ""
    source: str = ""


@dataclass
class Region:
    """An agroclimatic zone or administrative region."""
    id: str
    label: MultiLabel
    state: str = ""
    agroclimatic_zone: str = ""
    predominant_soils: list[SoilTypeEnum] = field(default_factory=list)
    avg_rainfall_mm: float = 0.0


# ─────────────────────────────────────────────────────────────
# Relationship Edges
# ─────────────────────────────────────────────────────────────

class RelationType(str, enum.Enum):
    """Edge types in the knowledge graph.

    Naming convention:  SUBJECT_verb_OBJECT
    All edges are directed from source → target.
    Edges marked [causal] encode causal directionality.
    """
    # Crop lifecycle
    HAS_STAGE             = "has_stage"              # Crop → CropStage
    REQUIRES_NUTRIENT     = "requires_nutrient"      # CropStage → Nutrient  [causal]

    # Threats
    VULNERABLE_TO_PEST    = "vulnerable_to_pest"     # CropStage → Pest
    VULNERABLE_TO_DISEASE = "vulnerable_to_disease"  # CropStage → Disease
    CAUSES_DISEASE        = "causes_disease"         # Pest → Disease (some pests vector diseases)

    # Interventions  [all causal edges]
    TREATS_PEST           = "treats_pest"             # Intervention → Pest   [causal]
    TREATS_DISEASE        = "treats_disease"          # Intervention → Disease [causal]
    PROVIDES_NUTRIENT     = "provides_nutrient"       # Intervention → Nutrient [causal]
    RECOMMENDED_FOR_STAGE = "recommended_for_stage"   # Intervention → CropStage [causal]

    # Safety constraints
    HAS_CONSTRAINT        = "has_constraint"          # Intervention → SafetyConstraint
    INCOMPATIBLE_WITH     = "incompatible_with"       # Intervention → Intervention (bidirectional)

    # Geography
    SUITABLE_FOR_REGION   = "suitable_for_region"     # Crop → Region
    AVAILABLE_IN          = "available_in"            # GovtScheme → Region
    APPLICABLE_TO_CROP    = "applicable_to_crop"      # GovtScheme → Crop


@dataclass(frozen=True)
class Edge:
    """A typed, directed edge in the knowledge graph."""
    source_id: str
    target_id: str
    relation: RelationType
    weight: float = 1.0                  # causal strength (0–1), default full
    evidence_source: str = ""            # ICAR/KVK citation for this edge
    metadata: dict = field(default_factory=dict)

    def __hash__(self):
        return hash((self.source_id, self.target_id, self.relation))

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return NotImplemented
        return (self.source_id == other.source_id
                and self.target_id == other.target_id
                and self.relation == other.relation)
