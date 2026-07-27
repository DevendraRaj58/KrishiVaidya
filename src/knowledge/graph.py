"""
CADI Knowledge Graph — Graph Engine

An in-memory, queryable agricultural knowledge graph built on NetworkX.
Supports typed entity nodes, causal directed edges, and efficient
subgraph retrieval for grounding LLM-generated advisory.

Design decisions:
  - NetworkX DiGraph for simplicity and zero external dependency.
    At our scale (~5K nodes, ~20K edges for 5 crops), this is sufficient.
  - All nodes carry their full entity dataclass as the `entity` attribute.
  - All edges carry their full Edge dataclass as edge data.
  - Serializable to/from JSON for persistence and versioning.
  - Thread-safe read access (immutable after load); writes require rebuild.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional, Type, Union

import networkx as nx

from .graph_schema import (
    Crop, CropStage, CropStageEnum, Disease, Edge, GovtScheme,
    Intervention, InterventionType, MultiLabel, Nutrient, Pest,
    Region, RelationType, SafetyConstraint, SeasonEnum,
    SeverityLevel, SoilTypeEnum,
)

logger = logging.getLogger(__name__)

# Entity type tag stored on each node for O(1) type filtering
_ENTITY_TYPE_KEY = "_entity_type"

# Map from entity type name → dataclass
_ENTITY_CLASSES: dict[str, Type] = {
    "Crop": Crop,
    "CropStage": CropStage,
    "Nutrient": Nutrient,
    "Pest": Pest,
    "Disease": Disease,
    "Intervention": Intervention,
    "SafetyConstraint": SafetyConstraint,
    "GovtScheme": GovtScheme,
    "Region": Region,
}


class AgriKnowledgeGraph:
    """In-memory agricultural knowledge graph.

    Usage::

        kg = AgriKnowledgeGraph()
        kg.add_entity(Crop(id="rice", label=MultiLabel(en="Rice", hi="चावल")))
        kg.add_edge(Edge("rice", "rice_flowering", RelationType.HAS_STAGE))
        interventions = kg.get_interventions_for("rice", CropStageEnum.FLOWERING)
    """

    def __init__(self) -> None:
        self._g = nx.DiGraph()
        self._entity_index: dict[str, Any] = {}   # id → entity dataclass

    # ─────────────────────────────────────────────────────
    # Mutation (used during load / build)
    # ─────────────────────────────────────────────────────

    def add_entity(self, entity: Any) -> None:
        """Add an entity node to the graph."""
        etype = type(entity).__name__
        if etype not in _ENTITY_CLASSES:
            raise TypeError(f"Unknown entity type: {etype}")
        self._g.add_node(entity.id, **{_ENTITY_TYPE_KEY: etype, "entity": entity})
        self._entity_index[entity.id] = entity

    def add_edge(self, edge: Edge) -> None:
        """Add a typed directed edge."""
        if edge.source_id not in self._g:
            logger.warning("Edge source %s not in graph; skipping", edge.source_id)
            return
        if edge.target_id not in self._g:
            logger.warning("Edge target %s not in graph; skipping", edge.target_id)
            return
        self._g.add_edge(
            edge.source_id,
            edge.target_id,
            relation=edge.relation,
            weight=edge.weight,
            evidence_source=edge.evidence_source,
            metadata=edge.metadata,
        )

    # ─────────────────────────────────────────────────────
    # Basic Queries
    # ─────────────────────────────────────────────────────

    def get_entity(self, entity_id: str) -> Optional[Any]:
        """Retrieve an entity by ID."""
        return self._entity_index.get(entity_id)

    def get_entities_by_type(self, entity_type: str) -> list[Any]:
        """Get all entities of a given type (e.g. 'Crop', 'Pest')."""
        return [
            data["entity"]
            for _, data in self._g.nodes(data=True)
            if data.get(_ENTITY_TYPE_KEY) == entity_type
        ]

    def get_neighbors(
        self,
        entity_id: str,
        relation: Optional[RelationType] = None,
        direction: str = "outgoing",
    ) -> list[tuple[Any, Edge]]:
        """Get neighboring entities connected by a specific relation.

        Args:
            entity_id: Source entity ID.
            relation: Filter by relation type. None = all relations.
            direction: "outgoing" (successors) or "incoming" (predecessors).

        Returns:
            List of (neighbor_entity, edge_data) tuples.
        """
        if entity_id not in self._g:
            return []

        results = []
        if direction == "outgoing":
            for _, target, data in self._g.out_edges(entity_id, data=True):
                if relation is None or data.get("relation") == relation:
                    entity = self._entity_index.get(target)
                    if entity:
                        edge = Edge(
                            source_id=entity_id,
                            target_id=target,
                            relation=data["relation"],
                            weight=data.get("weight", 1.0),
                            evidence_source=data.get("evidence_source", ""),
                            metadata=data.get("metadata", {}),
                        )
                        results.append((entity, edge))
        else:  # incoming
            for source, _, data in self._g.in_edges(entity_id, data=True):
                if relation is None or data.get("relation") == relation:
                    entity = self._entity_index.get(source)
                    if entity:
                        edge = Edge(
                            source_id=source,
                            target_id=entity_id,
                            relation=data["relation"],
                            weight=data.get("weight", 1.0),
                            evidence_source=data.get("evidence_source", ""),
                            metadata=data.get("metadata", {}),
                        )
                        results.append((entity, edge))
        return results

    # ─────────────────────────────────────────────────────
    # Domain-Specific Queries
    # ─────────────────────────────────────────────────────

    def get_crop_stages(self, crop_id: str) -> list[CropStage]:
        """Get all stages for a crop, ordered by typical_day_start."""
        stages = [
            entity for entity, _ in
            self.get_neighbors(crop_id, RelationType.HAS_STAGE)
        ]
        stages.sort(key=lambda s: s.typical_day_start)
        return stages

    def get_threats_for_stage(
        self, stage_id: str
    ) -> dict[str, list[Union[Pest, Disease]]]:
        """Get pests and diseases that threaten a specific crop stage."""
        pests = [
            entity for entity, _ in
            self.get_neighbors(stage_id, RelationType.VULNERABLE_TO_PEST)
        ]
        diseases = [
            entity for entity, _ in
            self.get_neighbors(stage_id, RelationType.VULNERABLE_TO_DISEASE)
        ]
        return {"pests": pests, "diseases": diseases}

    def get_interventions_for_stage(
        self, stage_id: str
    ) -> list[tuple[Intervention, Edge]]:
        """Get all interventions recommended for a crop stage."""
        return [
            (entity, edge)
            for entity, edge in
            self.get_neighbors(stage_id, RelationType.RECOMMENDED_FOR_STAGE, direction="incoming")
            if isinstance(entity, Intervention)
        ]

    def get_interventions_for_threat(
        self, threat_id: str
    ) -> list[tuple[Intervention, Edge]]:
        """Get interventions that treat a specific pest or disease."""
        pest_treatments = self.get_neighbors(
            threat_id, RelationType.TREATS_PEST, direction="incoming"
        )
        disease_treatments = self.get_neighbors(
            threat_id, RelationType.TREATS_DISEASE, direction="incoming"
        )
        return [
            (entity, edge)
            for entity, edge in pest_treatments + disease_treatments
            if isinstance(entity, Intervention)
        ]

    def get_safety_constraints(
        self, intervention_id: str
    ) -> list[tuple[SafetyConstraint, Edge]]:
        """Get all safety constraints for an intervention."""
        return [
            (entity, edge)
            for entity, edge in
            self.get_neighbors(intervention_id, RelationType.HAS_CONSTRAINT)
            if isinstance(entity, SafetyConstraint)
        ]

    def get_incompatible_interventions(
        self, intervention_id: str
    ) -> list[tuple[Intervention, Edge]]:
        """Get interventions that are chemically incompatible."""
        outgoing = [
            (entity, edge)
            for entity, edge in
            self.get_neighbors(intervention_id, RelationType.INCOMPATIBLE_WITH)
            if isinstance(entity, Intervention)
        ]
        incoming = [
            (entity, edge)
            for entity, edge in
            self.get_neighbors(intervention_id, RelationType.INCOMPATIBLE_WITH, direction="incoming")
            if isinstance(entity, Intervention)
        ]
        return outgoing + incoming

    def get_schemes_for_crop(
        self,
        crop_id: str,
        region_id: Optional[str] = None,
        as_of: Optional[date] = None,
    ) -> list[GovtScheme]:
        """Get valid government schemes for a crop, optionally filtered by region and date."""
        schemes = [
            entity
            for entity, _ in
            self.get_neighbors(crop_id, RelationType.APPLICABLE_TO_CROP, direction="incoming")
            if isinstance(entity, GovtScheme)
        ]

        if region_id:
            schemes = [
                s for s in schemes
                if not s.eligible_regions or region_id in s.eligible_regions
            ]

        if as_of:
            schemes = [
                s for s in schemes
                if (s.valid_from is None or s.valid_from <= as_of)
                and (s.valid_until is None or s.valid_until >= as_of)
            ]

        return schemes

    def get_nutrients_for_stage(self, stage_id: str) -> list[tuple[Nutrient, Edge]]:
        """Get nutrients required at a crop stage with causal edge data."""
        return [
            (entity, edge)
            for entity, edge in
            self.get_neighbors(stage_id, RelationType.REQUIRES_NUTRIENT)
            if isinstance(entity, Nutrient)
        ]

    def get_suitable_crops_for_region(self, region_id: str) -> list[Crop]:
        """Get crops suitable for a specific region."""
        return [
            entity
            for entity, _ in
            self.get_neighbors(region_id, RelationType.SUITABLE_FOR_REGION, direction="incoming")
            if isinstance(entity, Crop)
        ]

    # ─────────────────────────────────────────────────────
    # Subgraph Extraction (for LLM context grounding)
    # ─────────────────────────────────────────────────────

    def extract_context_subgraph(
        self,
        crop_id: str,
        stage: Optional[CropStageEnum] = None,
        symptoms: Optional[list[str]] = None,
    ) -> dict:
        """Extract a relevant subgraph for grounding an LLM advisory.

        Returns a serializable dict containing all entities and edges
        relevant to the given crop, stage, and symptoms. This is
        injected into the LLM prompt as structured context.
        """
        context: dict[str, Any] = {
            "crop": None,
            "stage": None,
            "nutrients": [],
            "threats": {"pests": [], "diseases": []},
            "interventions": [],
            "safety_constraints": [],
            "evidence_sources": set(),
        }

        crop = self.get_entity(crop_id)
        if not crop or not isinstance(crop, Crop):
            return context
        context["crop"] = {
            "id": crop.id,
            "name": crop.label.en,
            "seasons": [s.value for s in crop.seasons],
            "optimal_ph": f"{crop.optimal_ph_min}-{crop.optimal_ph_max}",
        }

        # Find the matching stage
        stage_entity = None
        if stage:
            for cs in self.get_crop_stages(crop_id):
                if cs.stage == stage:
                    stage_entity = cs
                    break

        if stage_entity:
            context["stage"] = {
                "id": stage_entity.id,
                "name": stage_entity.label.en,
                "stage": stage_entity.stage.value,
                "day_range": f"{stage_entity.typical_day_start}-{stage_entity.typical_day_end}",
                "critical_nutrients": stage_entity.critical_nutrients,
            }

            # Nutrients
            for nutrient, edge in self.get_nutrients_for_stage(stage_entity.id):
                context["nutrients"].append({
                    "name": nutrient.label.en,
                    "symbol": nutrient.symbol,
                    "source": edge.evidence_source,
                })
                if edge.evidence_source:
                    context["evidence_sources"].add(edge.evidence_source)

            # Threats
            threats = self.get_threats_for_stage(stage_entity.id)
            for pest in threats["pests"]:
                context["threats"]["pests"].append({
                    "name": pest.label.en,
                    "symptoms": pest.symptoms,
                })
            for disease in threats["diseases"]:
                context["threats"]["diseases"].append({
                    "name": disease.label.en,
                    "pathogen_type": disease.pathogen_type,
                    "symptoms": disease.symptoms,
                })

            # Interventions for this stage
            for intervention, edge in self.get_interventions_for_stage(stage_entity.id):
                intervention_data = {
                    "id": intervention.id,
                    "name": intervention.label.en,
                    "type": intervention.type.value,
                    "dosage": intervention.recommended_dosage,
                    "method": intervention.application_method,
                    "waiting_period_days": intervention.waiting_period_days,
                    "source": intervention.source,
                }
                # Attach safety constraints
                constraints = self.get_safety_constraints(intervention.id)
                intervention_data["safety_constraints"] = [
                    {"description": c.description, "severity": c.severity.value}
                    for c, _ in constraints
                ]
                context["interventions"].append(intervention_data)
                if intervention.source:
                    context["evidence_sources"].add(intervention.source)

        # Convert set to list for JSON serialization
        context["evidence_sources"] = list(context["evidence_sources"])
        return context

    # ─────────────────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────────────────

    def save(self, path: Union[str, Path]) -> None:
        """Serialize the graph to a JSON file."""
        path = Path(path)
        data = {
            "entities": {},
            "edges": [],
        }

        for node_id, node_data in self._g.nodes(data=True):
            etype = node_data[_ENTITY_TYPE_KEY]
            entity = node_data["entity"]
            entity_dict = _entity_to_dict(entity)
            data["entities"].setdefault(etype, []).append(entity_dict)

        for source, target, edge_data in self._g.edges(data=True):
            data["edges"].append({
                "source_id": source,
                "target_id": target,
                "relation": edge_data["relation"].value,
                "weight": edge_data.get("weight", 1.0),
                "evidence_source": edge_data.get("evidence_source", ""),
                "metadata": edge_data.get("metadata", {}),
            })

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info("Knowledge graph saved to %s (%d nodes, %d edges)",
                     path, self._g.number_of_nodes(), self._g.number_of_edges())

    @classmethod
    def load(cls, path: Union[str, Path]) -> AgriKnowledgeGraph:
        """Deserialize a graph from a JSON file."""
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        kg = cls()

        for etype, entities in data.get("entities", {}).items():
            entity_cls = _ENTITY_CLASSES.get(etype)
            if not entity_cls:
                logger.warning("Unknown entity type in data: %s", etype)
                continue
            for entity_dict in entities:
                entity = _dict_to_entity(entity_cls, entity_dict)
                kg.add_entity(entity)

        for edge_dict in data.get("edges", []):
            edge = Edge(
                source_id=edge_dict["source_id"],
                target_id=edge_dict["target_id"],
                relation=RelationType(edge_dict["relation"]),
                weight=edge_dict.get("weight", 1.0),
                evidence_source=edge_dict.get("evidence_source", ""),
                metadata=edge_dict.get("metadata", {}),
            )
            kg.add_edge(edge)

        logger.info("Knowledge graph loaded from %s (%d nodes, %d edges)",
                     path, kg._g.number_of_nodes(), kg._g.number_of_edges())
        return kg

    # ─────────────────────────────────────────────────────
    # Stats
    # ─────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        """Summary statistics for the knowledge graph."""
        type_counts: dict[str, int] = {}
        for _, data in self._g.nodes(data=True):
            etype = data.get(_ENTITY_TYPE_KEY, "unknown")
            type_counts[etype] = type_counts.get(etype, 0) + 1

        relation_counts: dict[str, int] = {}
        for _, _, data in self._g.edges(data=True):
            rel = data.get("relation", "unknown")
            key = rel.value if isinstance(rel, RelationType) else str(rel)
            relation_counts[key] = relation_counts.get(key, 0) + 1

        return {
            "total_nodes": self._g.number_of_nodes(),
            "total_edges": self._g.number_of_edges(),
            "entity_types": type_counts,
            "relation_types": relation_counts,
        }


# ─────────────────────────────────────────────────────────────
# Serialization Helpers
# ─────────────────────────────────────────────────────────────

def _entity_to_dict(entity: Any) -> dict:
    """Convert an entity dataclass to a JSON-serializable dict."""
    d = asdict(entity)
    # Convert enums to their values
    for key, value in d.items():
        if isinstance(value, enum.Enum):
            d[key] = value.value
        elif isinstance(value, list):
            d[key] = [v.value if isinstance(v, enum.Enum) else v for v in value]
        elif isinstance(value, date) and not isinstance(value, datetime):
            d[key] = value.isoformat()
    return d


def _dict_to_entity(entity_cls: Type, d: dict) -> Any:
    """Reconstruct an entity dataclass from a dict, handling enum coercion."""
    import inspect
    sig = inspect.signature(entity_cls)
    cleaned = {}

    for param_name, param in sig.parameters.items():
        if param_name not in d:
            continue
        value = d[param_name]
        annotation = param.annotation

        # Handle MultiLabel
        if annotation == MultiLabel and isinstance(value, dict):
            cleaned[param_name] = MultiLabel(**value)
        # Handle single enums
        elif isinstance(annotation, type) and issubclass(annotation, enum.Enum):
            cleaned[param_name] = annotation(value) if value else param.default
        # Handle list of enums
        elif hasattr(annotation, "__origin__") and annotation.__origin__ is list:
            args = getattr(annotation, "__args__", ())
            if args and isinstance(args[0], type) and issubclass(args[0], enum.Enum):
                cleaned[param_name] = [args[0](v) for v in value] if value else []
            else:
                cleaned[param_name] = value if value is not None else []
        # Handle Optional[date]
        elif param_name in ("valid_from", "valid_until") and isinstance(value, str):
            cleaned[param_name] = date.fromisoformat(value) if value else None
        else:
            cleaned[param_name] = value

    return entity_cls(**cleaned)


# Expose a convenience alias
import enum  # noqa: E402 — already imported but needed at module scope
