"""
CADI Attribution Engine — Evidence Retriever (Component ⑤, Part 2)

Matches extracted claims against the Knowledge Graph to find supporting evidence.
"""

import logging
from typing import List
from ..models.advisory import AtomicClaim, Evidence
from ..knowledge.graph import AgriKnowledgeGraph

logger = logging.getLogger(__name__)

class EvidenceRetriever:
    """Retrieves supporting evidence from the Knowledge Graph for a claim."""

    def __init__(self, kg: AgriKnowledgeGraph):
        self._kg = kg

    def retrieve_evidence(self, claim: AtomicClaim) -> List[Evidence]:
        """
        Retrieves evidence from the KG that supports or refutes the claim.
        """
        evidence_list = []
        
        # Extremely simple matching for the prototype:
        # Check if the entities mentioned in the claim exist in the KG.
        # Find edges between them.
        
        found_entities = set()
        for entity_str in claim.entities:
            query = entity_str.lower().strip()
            if not query or len(query) < 3:
                continue
                
            # Search KG for entity matching string
            for node_id, data in self._kg._g.nodes(data=True):
                entity_obj = data.get("entity")
                if entity_obj:
                    label_text = ""
                    if hasattr(entity_obj, "label"):
                        label_text = entity_obj.label.en.lower()
                    id_text = str(entity_obj.id).replace("_", " ").lower()
                    
                    if query in label_text or query in id_text or label_text in query:
                        found_entities.add(node_id)
        
        found_entities = list(found_entities)
        
        # If we found multiple entities, look for edges between them
        for i in range(len(found_entities)):
            for j in range(i + 1, len(found_entities)):
                u, v = found_entities[i], found_entities[j]
                
                # Check u -> v
                if self._kg._g.has_edge(u, v):
                    edge_data = self._kg._g.get_edge_data(u, v)
                    evidence_list.append(Evidence(
                        source_id=u,
                        target_id=v,
                        relation=str(edge_data.get("relation", "")),
                        relevance_score=0.9,
                        source_citation=edge_data.get("evidence_source", "ICAR Base Knowledge"),
                        text_snippet=f"{u} -> {v} ({edge_data.get('relation')})"
                    ))
                
                # Check v -> u
                if self._kg._g.has_edge(v, u):
                    edge_data = self._kg._g.get_edge_data(v, u)
                    evidence_list.append(Evidence(
                        source_id=v,
                        target_id=u,
                        relation=str(edge_data.get("relation", "")),
                        relevance_score=0.9,
                        source_citation=edge_data.get("evidence_source", "ICAR Base Knowledge"),
                        text_snippet=f"{v} -> {u} ({edge_data.get('relation')})"
                    ))
        
        # If no direct edges but single entities found, provide weak evidence
        if not evidence_list and found_entities:
            for u in found_entities:
                evidence_list.append(Evidence(
                    source_id=u,
                    target_id="",
                    relation="entity_match",
                    relevance_score=0.5,
                    source_citation="CADI Knowledge Graph",
                    text_snippet=f"Entity {u} exists in KG."
                ))

        return evidence_list
