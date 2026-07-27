"""
CADI Interface — Formatter (Component ⑪)

Formats the AttributedAdvisory into HTML for Telegram.
"""

from ..models.advisory import AttributedAdvisory

def format_advisory_html(advisory: AttributedAdvisory) -> str:
    """
    Renders the advisory with citations and safety badges.
    """
    html = f"<b>{advisory.headline}</b>\n"
    html += f"<i>Stage: {advisory.stage}</i>\n\n"
    
    # Safety badge
    if advisory.is_safe:
        html += "✅ <b>SAFETY VERIFIED</b>\n"
    else:
        html += "❌ <b>SAFETY BLOCKED</b>\n"
        for v in advisory.safety_violations:
            html += f"⚠️ {v}\n"
        return html
    
    # Body with claims
    for scored_claim in advisory.claims:
        # Append citation markers if grounded
        citations = []
        for ev in scored_claim.evidence:
            # Find citation id in the advisory's global citation list
            for cit in advisory.citations:
                if cit.text == ev.source_citation:
                    citations.append(f"[{cit.id}]")
                    break
        
        cit_text = "".join(set(citations))
        
        if scored_claim.status == "GROUNDED":
            html += f"• {scored_claim.claim.text} {cit_text}\n"
        elif scored_claim.status == "WEAKLY_GROUNDED":
            html += f"• {scored_claim.claim.text} {cit_text} <i>(Weak evidence)</i>\n"
        else:
            html += f"• {scored_claim.claim.text} <i>(Unverified)</i>\n"
            
    # Sources section
    if advisory.citations:
        html += "\n<b>Sources:</b>\n"
        for cit in advisory.citations:
            html += f"[{cit.id}] {cit.text}\n"
            
    if advisory.needs_human_review:
        html += "\n👨‍🌾 <i>This advisory requires human expert review due to low confidence.</i>\n"
        
    return html
