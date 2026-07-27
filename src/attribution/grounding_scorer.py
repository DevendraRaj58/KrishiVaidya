"""
CADI Attribution Engine — Grounding Scorer (Component ⑤, Part 3)

Evaluates claim validity against retrieved evidence.
"""

import logging
from typing import List
from ..models.advisory import AtomicClaim, Evidence, ScoredClaim

logger = logging.getLogger(__name__)

class GroundingScorer:
    """Scores how well a claim is supported by evidence."""

    def score_claim(self, claim: AtomicClaim, evidence: List[Evidence]) -> ScoredClaim:
        """
        Score a claim based on the retrieved evidence.
        """
        if not evidence:
            return ScoredClaim(
                claim=claim,
                evidence=[],
                grounding_score=0.0,
                status="UNGROUNDED"
            )
            
        max_score = max([e.relevance_score for e in evidence])
        
        if max_score >= 0.8:
            status = "GROUNDED"
        elif max_score >= 0.5:
            status = "WEAKLY_GROUNDED"
        else:
            status = "UNGROUNDED"
            
        return ScoredClaim(
            claim=claim,
            evidence=evidence,
            grounding_score=max_score,
            status=status
        )
