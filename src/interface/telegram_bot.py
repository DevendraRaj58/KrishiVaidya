"""
CADI Interface — Telegram Bot

Hooks the CADI graph into the Telegram bot interface.
"""

import logging
from .formatter import format_advisory_html

logger = logging.getLogger(__name__)

class TelegramBot:
    """Stub Telegram Bot for CADI."""
    
    def __init__(self, cadi_graph):
        self.graph = cadi_graph
        
    def handle_message(self, chat_id: str, text: str):
        """
        Processes an incoming message through the CADI graph.
        """
        # Set up state
        state = {
            "context": {"crop": "rice", "stage": "flowering"},
            "raw_advisory_text": text
        }
        
        # Run graph
        # For prototype, we simulate a graph run
        final_state = self.graph.invoke(state)
        
        # Format and send
        advisory = final_state.get("advisory")
        if advisory:
            html = format_advisory_html(advisory)
            logger.info(f"Sending to {chat_id}:\n{html}")
            return html
        return "Sorry, I couldn't generate an advisory."
