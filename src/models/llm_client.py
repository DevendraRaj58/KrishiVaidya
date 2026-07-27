"""
CADI Models - LLM Client Wrapper
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    """Wrapper for interacting with the LLM API (OpenAI or compatible)."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        # Relies on OPENAI_API_KEY being set in the environment
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment. LLM calls may fail.")
            
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model_name = model_name

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Generate plain text output."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM text generation failed: {e}")
            raise e

    async def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> Any:
        """Generate structured JSON output."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                return {}
            
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
                
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"LLM JSON generation failed: {e}")
            raise e
