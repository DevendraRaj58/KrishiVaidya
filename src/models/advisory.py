"""
CADI Models - Advisory & Claims
"""
from dataclasses import dataclass, field
from typing import List, Optional
from ..knowledge.graph_schema import SeverityLevel

@dataclass
class AtomicClaim:
    """A decomposed, atomic factual or actionable claim."""
    id: str
    text: str
    claim_type: str  # "ACTIONABLE", "FACTUAL", "CAUSAL", "TEMPORAL"
    entities: List[str] = field(default_factory=list)

@dataclass
class Evidence:
    """Evidence retrieved from Knowledge Graph supporting a claim."""
    source_id: str
    target_id: str
    relation: str
    relevance_score: float
    source_citation: str
    text_snippet: str = ""

@dataclass
class ScoredClaim:
    """A claim evaluated against retrieved evidence."""
    claim: AtomicClaim
    evidence: List[Evidence]
    grounding_score: float
    status: str  # "GROUNDED", "WEAKLY_GROUNDED", "UNGROUNDED"

@dataclass
class Citation:
    """A formatted citation for final advisory display."""
    id: int
    text: str

@dataclass
class GroundingMetrics:
    """Aggregate metrics for advisory grounding."""
    total_claims: int
    grounded_claims: int
    weakly_grounded_claims: int
    ungrounded_claims: int
    mean_score: float

@dataclass
class AttributedAdvisory:
    """Final advisory structure sent to farmer."""
    headline: str
    stage: str
    claims: List[ScoredClaim] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    grounding_metrics: Optional[GroundingMetrics] = None
    is_safe: bool = True
    safety_violations: List[str] = field(default_factory=list)
    needs_human_review: bool = False
