"""
CADI Attribution Engine — Claim Extractor (Component ⑤, Part 1)

Decomposes a generated advisory into individual factual and actionable claims.
"""

import json
import logging
import re
from typing import List
from ..models.advisory import AtomicClaim

logger = logging.getLogger(__name__)

class ClaimExtractor:
    """Extracts atomic claims from a generated advisory."""
    
    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: The LLM client to use for extraction.
        """
        self.llm_client = llm_client

    async def extract_claims(self, advisory_text: str) -> List[AtomicClaim]:
        """
        Decompose advisory text into atomic claims.
        """
        if not self.llm_client:
            logger.warning("No LLM client provided. Returning dummy claims.")
            return self._fallback_extraction(advisory_text)
            
        system_prompt = (
            "You are an agricultural expert system. Decompose the following advisory "
            "into atomic claims. For each claim, provide:\n"
            "- 'text': The atomic claim text.\n"
            "- 'claim_type': 'ACTIONABLE', 'FACTUAL', 'CAUSAL', or 'TEMPORAL'.\n"
            "- 'entities': A list of key entities (crop, chemical, disease, pest, nutrient).\n\n"
            "Output strictly a JSON object containing a single key 'claims' which maps to a list of these claim objects."
        )
        
        try:
            # Here we assume llm_client has a method for json generation
            response = await self.llm_client.generate_json(system_prompt, advisory_text)
            claims_data = response.get("claims", [])
            claims = []
            for i, item in enumerate(claims_data):
                claims.append(
                    AtomicClaim(
                        id=f"claim_{i}",
                        text=item.get("text", ""),
                        claim_type=item.get("claim_type", "FACTUAL"),
                        entities=item.get("entities", [])
                    )
                )
            return claims
        except Exception as e:
            logger.error(f"Error extracting claims: {e}")
            return self._fallback_extraction(advisory_text)

    def _fallback_extraction(self, text: str) -> List[AtomicClaim]:
        """Simple regex-based sentence splitting as fallback."""
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 5]
        return [
            AtomicClaim(
                id=f"claim_{i}",
                text=sentence,
                claim_type="ACTIONABLE" if any(w in sentence.lower() for w in ["apply", "use", "spray"]) else "FACTUAL",
                entities=[]
            )
            for i, sentence in enumerate(sentences)
        ]
