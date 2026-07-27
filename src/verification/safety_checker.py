"""
CADI Verification Layer — Symbolic Safety Checker (Component ⑩)

A rule-based verification engine that formally checks every AI-generated
agricultural recommendation against the Knowledge Graph before it
reaches the farmer.

This is the core patentable component: a symbolic constraint verification
engine interposed between neural advisory generation and user delivery,
operating over a domain-specific agricultural knowledge graph.

Architecture:
  Neural LLM → [generates advisory text]
       ↓
  SafetyChecker → [decomposes into claims]
       ↓
  Rule Engine → [checks each claim against KG constraints]
       ↓
  SafetyVerdict → {safe: bool, violations: [...], warnings: [...]}
       ↓
  If safe → deliver to farmer with citations
  If unsafe → reformulate OR escalate to human

Design principles:
  - Conservative: when in doubt, flag as warning (not violation)
  - Explainable: every violation includes the specific rule and KG edge
  - Fast: O(1) graph lookups, no ML inference in the safety path
  - Extensible: new rules are plain Python functions
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from ..knowledge.graph import AgriKnowledgeGraph
from ..knowledge.graph_schema import (
    CropStageEnum, Intervention, InterventionType, SafetyConstraint,
    SeverityLevel, RelationType,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Output Types
# ─────────────────────────────────────────────────────────────

@dataclass
class Violation:
    """A specific safety rule violation found in the advisory."""
    rule_id: str
    severity: SeverityLevel
    description: str
    evidence_source: str              # KG source for the rule
    offending_text: str = ""          # The advisory text that triggered it
    suggested_fix: str = ""           # How to correct the recommendation


@dataclass
class SafetyVerdict:
    """The result of safety checking an advisory."""
    is_safe: bool
    violations: list[Violation] = field(default_factory=list)
    warnings: list[Violation] = field(default_factory=list)
    checked_rules: int = 0
    advisory_text: str = ""           # Original text checked

    @property
    def critical_violations(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == SeverityLevel.HIGH]

    @property
    def summary(self) -> str:
        if self.is_safe:
            return f"✅ SAFE — {self.checked_rules} rules checked, {len(self.warnings)} warnings"
        return (
            f"❌ UNSAFE — {len(self.violations)} violations "
            f"({len(self.critical_violations)} critical), "
            f"{len(self.warnings)} warnings"
        )


# ─────────────────────────────────────────────────────────────
# Safety Checker Engine
# ─────────────────────────────────────────────────────────────

class SafetyChecker:
    """Symbolic safety verification engine.

    Checks generated advisory text against Knowledge Graph constraints.
    Uses pattern matching to detect mentions of interventions, then
    verifies each against KG safety rules.

    Usage::

        checker = SafetyChecker(knowledge_graph)
        verdict = checker.check(
            advisory_text="Apply Urea 100kg/ha...",
            crop_id="rice",
            stage=CropStageEnum.FLOWERING,
            farmer_current_chemicals=["rice_trichoderma"],
            days_to_harvest=15,
        )
        if not verdict.is_safe:
            # Reformulate or escalate
    """

    def __init__(self, kg: AgriKnowledgeGraph) -> None:
        self._kg = kg
        self._rules: list[_SafetyRule] = [
            _DosageLimitRule(),
            _ChemicalCompatibilityRule(),
            _PreHarvestIntervalRule(),
            _StageAppropriatenessRule(),
            _BiologicalChemicalConflictRule(),
            _NitrogenExcessRule(),
            _BeePollinatorSafetyRule(),
            _SchemeValidityRule(),
            _GenericConstraintRule(),
        ]

    def check(
        self,
        advisory_text: str,
        crop_id: str,
        stage: Optional[CropStageEnum] = None,
        farmer_current_chemicals: Optional[list[str]] = None,
        days_to_harvest: Optional[int] = None,
        current_date: Optional[date] = None,
        weather_context: Optional[dict] = None,
    ) -> SafetyVerdict:
        """Run all safety rules against the advisory text.

        Args:
            advisory_text: The generated advisory to check.
            crop_id: Current crop ID.
            stage: Current crop stage.
            farmer_current_chemicals: IDs of chemicals farmer has recently applied.
            days_to_harvest: Estimated days until harvest.
            current_date: For scheme validity checking.
            weather_context: Weather data for timing rules.

        Returns:
            SafetyVerdict with all violations and warnings.
        """
        context = _CheckContext(
            kg=self._kg,
            advisory_text=advisory_text,
            crop_id=crop_id,
            stage=stage,
            farmer_current_chemicals=farmer_current_chemicals or [],
            days_to_harvest=days_to_harvest,
            current_date=current_date or date.today(),
            weather_context=weather_context or {},
            mentioned_interventions=self._extract_mentioned_interventions(advisory_text),
        )

        violations: list[Violation] = []
        warnings: list[Violation] = []
        checked = 0

        for rule in self._rules:
            try:
                result = rule.check(context)
                checked += 1
                for v in result:
                    if v.severity == SeverityLevel.HIGH:
                        violations.append(v)
                    else:
                        warnings.append(v)
            except Exception as e:
                logger.error("Safety rule %s failed: %s", rule.name, e)
                # Fail-safe: if a rule crashes, add a warning
                warnings.append(Violation(
                    rule_id=f"{rule.name}_error",
                    severity=SeverityLevel.MEDIUM,
                    description=f"Safety rule '{rule.name}' could not be evaluated: {e}",
                    evidence_source="CADI Safety Engine",
                ))

        is_safe = len(violations) == 0

        verdict = SafetyVerdict(
            is_safe=is_safe,
            violations=violations,
            warnings=warnings,
            checked_rules=checked,
            advisory_text=advisory_text,
        )

        if not is_safe:
            logger.warning("Advisory UNSAFE: %s", verdict.summary)
            for v in violations:
                logger.warning("  VIOLATION [%s]: %s", v.rule_id, v.description)
        else:
            logger.info("Advisory SAFE: %s", verdict.summary)

        return verdict

    def _extract_mentioned_interventions(self, text: str) -> list[Intervention]:
        """Extract interventions mentioned in the advisory text by matching
        against known intervention names in the KG."""
        mentioned = []
        text_lower = text.lower()
        for intervention in self._kg.get_entities_by_type("Intervention"):
            # Extract base names to handle variations in LLM text
            id_parts = intervention.id.split('_')[1:] # cotton_monocrotophos -> monocrotophos
            id_term = " ".join(id_parts).lower()
            ai_term = intervention.active_ingredient.split(' ')[0].lower() # Monocrotophos 36% -> monocrotophos
            
            terms = [
                id_term,
                ai_term,
                intervention.label.en.lower(),
                intervention.active_ingredient.lower(),
            ]
            for term in terms:
                if term and len(term) > 3 and term in text_lower:
                    if intervention not in mentioned:
                        mentioned.append(intervention)
                    break
        return mentioned


# ─────────────────────────────────────────────────────────────
# Check Context (internal data object passed to rules)
# ─────────────────────────────────────────────────────────────

@dataclass
class _CheckContext:
    kg: AgriKnowledgeGraph
    advisory_text: str
    crop_id: str
    stage: Optional[CropStageEnum]
    farmer_current_chemicals: list[str]
    days_to_harvest: Optional[int]
    current_date: date
    weather_context: dict
    mentioned_interventions: list[Intervention]


# ─────────────────────────────────────────────────────────────
# Safety Rules (each is a self-contained checker)
# ─────────────────────────────────────────────────────────────

class _SafetyRule:
    """Base class for safety rules."""
    name: str = "base_rule"

    def check(self, ctx: _CheckContext) -> list[Violation]:
        raise NotImplementedError


class _DosageLimitRule(_SafetyRule):
    """Check if any mentioned dosage exceeds KG-defined bounds."""
    name = "dosage_limit"

    def check(self, ctx: _CheckContext) -> list[Violation]:
        violations = []
        # Look for numeric dosage patterns in text
        dosage_patterns = re.findall(
            r'(\d+(?:\.\d+)?)\s*(kg/ha|g/L|ml/L|kg|g|ml|L)',
            ctx.advisory_text, re.IGNORECASE
        )

        for intervention in ctx.mentioned_interventions:
            if intervention.recommended_dosage_max <= 0:
                continue  # No dosage bounds defined

            for amount_str, unit in dosage_patterns:
                amount = float(amount_str)
                # Only compare if units match
                if unit.lower() in intervention.dosage_unit.lower():
                    if amount > intervention.recommended_dosage_max * 1.2:  # 20% tolerance
                        violations.append(Violation(
                            rule_id=f"dosage_excess_{intervention.id}",
                            severity=SeverityLevel.HIGH,
                            description=(
                                f"Recommended dosage of {intervention.label.en} is "
                                f"{intervention.recommended_dosage_min}-{intervention.recommended_dosage_max} "
                                f"{intervention.dosage_unit}, but advisory suggests {amount} {unit}"
                            ),
                            evidence_source=intervention.source,
                            offending_text=f"{amount_str} {unit}",
                            suggested_fix=f"Reduce to {intervention.recommended_dosage_max} {intervention.dosage_unit}",
                        ))
        return violations


class _ChemicalCompatibilityRule(_SafetyRule):
    """Check if recommended chemicals are incompatible with each other
    or with farmer's recently applied chemicals."""
    name = "chemical_compatibility"

    def check(self, ctx: _CheckContext) -> list[Violation]:
        violations = []
        mentioned_ids = {i.id for i in ctx.mentioned_interventions}
        all_ids = mentioned_ids | set(ctx.farmer_current_chemicals)

        # Check pairwise incompatibilities
        for intervention in ctx.mentioned_interventions:
            incompatible = ctx.kg.get_incompatible_interventions(intervention.id)
            for incompat_entity, edge in incompatible:
                if incompat_entity.id in all_ids:
                    is_current = incompat_entity.id in ctx.farmer_current_chemicals
                    violations.append(Violation(
                        rule_id=f"incompatible_{intervention.id}_{incompat_entity.id}",
                        severity=SeverityLevel.HIGH,
                        description=(
                            f"{intervention.label.en} is INCOMPATIBLE with "
                            f"{incompat_entity.label.en}"
                            f"{' (recently applied by farmer)' if is_current else ' (also recommended in this advisory)'}. "
                            f"Do NOT use together."
                        ),
                        evidence_source=edge.evidence_source,
                        offending_text=intervention.label.en,
                        suggested_fix=f"Remove one of: {intervention.label.en} or {incompat_entity.label.en}",
                    ))
        return violations


class _PreHarvestIntervalRule(_SafetyRule):
    """Check if recommended chemicals violate pre-harvest waiting periods."""
    name = "pre_harvest_interval"

    def check(self, ctx: _CheckContext) -> list[Violation]:
        violations = []
        if ctx.days_to_harvest is None:
            return violations

        for intervention in ctx.mentioned_interventions:
            if intervention.waiting_period_days > 0:
                if ctx.days_to_harvest < intervention.waiting_period_days:
                    violations.append(Violation(
                        rule_id=f"phi_{intervention.id}",
                        severity=SeverityLevel.HIGH,
                        description=(
                            f"{intervention.label.en} has a pre-harvest interval of "
                            f"{intervention.waiting_period_days} days, but harvest is estimated "
                            f"in {ctx.days_to_harvest} days. Application now would leave "
                            f"unsafe residue levels on the crop."
                        ),
                        evidence_source=intervention.source,
                        offending_text=intervention.label.en,
                        suggested_fix=f"Do NOT apply. Consider non-chemical alternatives.",
                    ))
        return violations


class _StageAppropriatenessRule(_SafetyRule):
    """Check if recommended interventions are appropriate for the current crop stage."""
    name = "stage_appropriateness"

    def check(self, ctx: _CheckContext) -> list[Violation]:
        violations = []
        if not ctx.stage:
            return violations

        # Find the stage entity ID for current crop+stage
        stage_entities = ctx.kg.get_crop_stages(ctx.crop_id)
        current_stage_id = None
        for se in stage_entities:
            if se.stage == ctx.stage:
                current_stage_id = se.id
                break

        if not current_stage_id:
            return violations

        for intervention in ctx.mentioned_interventions:
            # Check if this intervention is recommended for the current stage
            recommended_stages = ctx.kg.get_neighbors(
                intervention.id,
                relation=None,
                direction="outgoing",
            )
            recommended_stage_ids = {
                entity.id for entity, edge in recommended_stages
                if hasattr(entity, 'stage')
            }

            if recommended_stage_ids and current_stage_id not in recommended_stage_ids:
                # Intervention is known but not recommended for this stage
                violations.append(Violation(
                    rule_id=f"stage_mismatch_{intervention.id}",
                    severity=SeverityLevel.MEDIUM,
                    description=(
                        f"{intervention.label.en} is not typically recommended for "
                        f"the {ctx.stage.value} stage of {ctx.crop_id}. "
                        f"Recommended stages: {', '.join(recommended_stage_ids)}"
                    ),
                    evidence_source=intervention.source or "CADI Knowledge Graph",
                    offending_text=intervention.label.en,
                ))
        return violations


class _BiologicalChemicalConflictRule(_SafetyRule):
    """Check if biological agents and chemical pesticides/fungicides
    are recommended together (they shouldn't be within 7 days)."""
    name = "biological_chemical_conflict"

    def check(self, ctx: _CheckContext) -> list[Violation]:
        violations = []
        biologicals = [i for i in ctx.mentioned_interventions
                       if i.type == InterventionType.BIOLOGICAL]
        chemicals = [i for i in ctx.mentioned_interventions
                     if i.type in (InterventionType.PESTICIDE, InterventionType.FUNGICIDE, InterventionType.HERBICIDE)]

        for bio in biologicals:
            for chem in chemicals:
                violations.append(Violation(
                    rule_id=f"bio_chem_conflict_{bio.id}_{chem.id}",
                    severity=SeverityLevel.HIGH,
                    description=(
                        f"Biological agent {bio.label.en} should NOT be applied together with "
                        f"chemical {chem.label.en}. Chemical will kill the biological agent. "
                        f"Maintain at least 7-day gap between applications."
                    ),
                    evidence_source="ICAR-NBAIR Bio-agent Compatibility Guide",
                    offending_text=f"{bio.label.en} + {chem.label.en}",
                    suggested_fix="Apply biological first, wait 7 days, then apply chemical if needed.",
                ))
        return violations


class _NitrogenExcessRule(_SafetyRule):
    """Check if total recommended nitrogen exceeds crop-specific limits."""
    name = "nitrogen_excess"

    _NITROGEN_LIMITS_KG_HA = {
        "rice": 120,
        "wheat": 150,
        "cotton": 160,
        "sugarcane": 300,
        "soybean": 30,   # legume — minimal N needed
    }

    def check(self, ctx: _CheckContext) -> list[Violation]:
        violations = []
        limit = self._NITROGEN_LIMITS_KG_HA.get(ctx.crop_id)
        if not limit:
            return violations

        # Check if advisory text mentions total N exceeding limit
        text_lower = ctx.advisory_text.lower()
        n_patterns = re.findall(r'(\d+)\s*kg\s*/?\s*ha.*(?:urea|nitrogen|n\b)', text_lower)
        for amount_str in n_patterns:
            amount = float(amount_str)
            # Urea is 46% N, DAP is 18% N
            if "urea" in text_lower:
                effective_n = amount * 0.46
            else:
                effective_n = amount
            if effective_n > limit:
                violations.append(Violation(
                    rule_id=f"nitrogen_excess_{ctx.crop_id}",
                    severity=SeverityLevel.HIGH,
                    description=(
                        f"Total nitrogen appears to exceed {limit} kg/ha limit for {ctx.crop_id}. "
                        f"Excess nitrogen increases pest/disease susceptibility and lodging."
                    ),
                    evidence_source=f"ICAR recommended N dose for {ctx.crop_id}",
                    offending_text=f"{amount_str} kg/ha",
                ))
        return violations


class _BeePollinatorSafetyRule(_SafetyRule):
    """Check if neonicotinoids are recommended during flowering stage."""
    name = "bee_pollinator_safety"

    _NEONICOTINOIDS = {"imidacloprid", "thiamethoxam", "clothianidin", "acetamiprid"}

    def check(self, ctx: _CheckContext) -> list[Violation]:
        violations = []
        if ctx.stage != CropStageEnum.FLOWERING:
            return violations

        for intervention in ctx.mentioned_interventions:
            ai = intervention.active_ingredient.lower()
            for neonic in self._NEONICOTINOIDS:
                if neonic in ai:
                    violations.append(Violation(
                        rule_id=f"bee_safety_{intervention.id}",
                        severity=SeverityLevel.HIGH,
                        description=(
                            f"{intervention.label.en} contains {neonic} (neonicotinoid), "
                            f"which is TOXIC TO BEES. Do NOT apply during flowering stage "
                            f"when pollinators are active."
                        ),
                        evidence_source="CIB&RC Environmental Safety Data; ICAR Pollinator Guidelines",
                        offending_text=intervention.label.en,
                        suggested_fix="Use non-neonicotinoid alternative or apply in evening when bees are less active.",
                    ))
        return violations


class _SchemeValidityRule(_SafetyRule):
    """Check if any mentioned government schemes are still valid."""
    name = "scheme_validity"

    def check(self, ctx: _CheckContext) -> list[Violation]:
        violations = []
        schemes = ctx.kg.get_entities_by_type("GovtScheme")
        text_lower = ctx.advisory_text.lower()

        for scheme in schemes:
            scheme_name = scheme.label.en.lower()
            if scheme_name in text_lower or scheme.id.replace("_", " ") in text_lower:
                if scheme.valid_until and scheme.valid_until < ctx.current_date:
                    violations.append(Violation(
                        rule_id=f"scheme_expired_{scheme.id}",
                        severity=SeverityLevel.HIGH,
                        description=(
                            f"Government scheme '{scheme.label.en}' expired on "
                            f"{scheme.valid_until.isoformat()}. Do NOT recommend expired schemes."
                        ),
                        evidence_source=scheme.source,
                        offending_text=scheme.label.en,
                        suggested_fix="Remove scheme reference or check for successor scheme.",
                    ))
        return violations


class _GenericConstraintRule(_SafetyRule):
    """Check explicit HAS_CONSTRAINT edges for any mentioned intervention."""
    name = "generic_constraint"

    def check(self, ctx: _CheckContext) -> list[Violation]:
        violations = []
        for intervention in ctx.mentioned_interventions:
            # Look up HAS_CONSTRAINT edges for this intervention
            constraints = ctx.kg.get_neighbors(
                intervention.id,
                relation=RelationType.HAS_CONSTRAINT,
                direction="outgoing"
            )
            for entity, edge in constraints:
                if isinstance(entity, SafetyConstraint):
                    # Flag every explicit constraint attached to the recommended intervention.
                    violations.append(Violation(
                        rule_id=f"constraint_{intervention.id}_{entity.id}",
                        severity=entity.severity,
                        description=(
                            f"Safety Constraint for {intervention.label.en}: "
                            f"{entity.description}"
                        ),
                        evidence_source=entity.source,
                        offending_text=intervention.label.en,
                        suggested_fix="Ensure recommendation strictly adheres to this constraint.",
                    ))
        return violations
