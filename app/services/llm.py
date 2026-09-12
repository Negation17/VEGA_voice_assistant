import logging
from typing import Optional
from openai import OpenAI
from app.config import settings

logger = logging.getLogger("vega.llm")

class LLMService:
    """Manages conversational interactions with LLM models."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.LLM_MODEL
        self._client = None

    @property
    def client(self) -> Optional[OpenAI]:
        if self._client is None and self.api_key:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    async def generate_answer(self, question: str) -> str:
        """Generate answer for user question."""
        if not question or not question.strip():
            return ""

        if not self.client:
            logger.warning("OPENAI_API_KEY is not configured. Using fallback local response.")
            return f"VEGA received your query: '{question}'. Please configure OPENAI_API_KEY for dynamic answers."

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": settings.SYSTEM_PROMPT},
                    {"role": "user", "content": question}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error querying OpenAI: {e}")
            return f"I encountered an error generating a response: {str(e)}"

llm_service = LLMService()
