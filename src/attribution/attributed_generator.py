"""
CADI Attribution Engine — Attributed Generator (Component ⑤, Part 4)

Combines claims and evidence into a final attributed advisory with citations.
"""

import logging
from typing import List
from ..models.advisory import (
    AtomicClaim, AttributedAdvisory, Citation, 
    GroundingMetrics, ScoredClaim
)
from .claim_extractor import ClaimExtractor
from .evidence_retriever import EvidenceRetriever
from .grounding_scorer import GroundingScorer
from ..knowledge.graph import AgriKnowledgeGraph

logger = logging.getLogger(__name__)

class AttributedGenerator:
    """Generates the final attributed advisory."""

    def __init__(self, kg: AgriKnowledgeGraph, llm_client=None):
        self._extractor = ClaimExtractor(llm_client)
        self._retriever = EvidenceRetriever(kg)
        self._scorer = GroundingScorer()

    async def generate(self, raw_advisory_text: str, headline: str, stage: str) -> AttributedAdvisory:
        """
        Pipeline: extract -> retrieve -> score -> build advisory.
        """
        claims = await self._extractor.extract_claims(raw_advisory_text)
        
        scored_claims = []
        citations_map = {}
        citation_counter = 1
        citations_list = []
        
        grounded_count = 0
        weak_count = 0
        ungrounded_count = 0
        total_score = 0.0
        
        for claim in claims:
            evidence = self._retriever.retrieve_evidence(claim)
            scored = self._scorer.score_claim(claim, evidence)
            scored_claims.append(scored)
            
            total_score += scored.grounding_score
            if scored.status == "GROUNDED":
                grounded_count += 1
            elif scored.status == "WEAKLY_GROUNDED":
                weak_count += 1
            else:
                ungrounded_count += 1
                
            # Assign citations
            for ev in scored.evidence:
                if ev.source_citation not in citations_map:
                    citations_map[ev.source_citation] = citation_counter
                    citations_list.append(Citation(id=citation_counter, text=ev.source_citation))
                    citation_counter += 1

        total_claims = len(claims)
        mean_score = total_score / total_claims if total_claims > 0 else 0.0
        
        metrics = GroundingMetrics(
            total_claims=total_claims,
            grounded_claims=grounded_count,
            weakly_grounded_claims=weak_count,
            ungrounded_claims=ungrounded_count,
            mean_score=mean_score
        )
        
        # If too many ungrounded claims, flag for human review
        needs_review = ungrounded_count > 0 or mean_score < 0.5
        
        return AttributedAdvisory(
            headline=headline,
            stage=stage,
            claims=scored_claims,
            citations=citations_list,
            grounding_metrics=metrics,
            needs_human_review=needs_review
        )
