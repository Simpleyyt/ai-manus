from typing import Any, Dict, List, Optional, Protocol
from app.domain.models.message import LLMMessage


class LLM(Protocol):
    """LLM gateway interface.

    Abstracts the underlying model framework (LangChain, raw SDK, …) away from
    the domain. Implementations live in ``infrastructure/external/llm`` and are
    responsible for translating :class:`LLMMessage` to/from framework types,
    tool binding, JSON repair and retries.
    """

    async def ask(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[str] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMMessage:
        """Send a chat request and return the assistant message.

        Args:
            messages: Full conversation context as domain messages.
            tools: Optional OpenAI-style function schemas for tool calling.
            response_format: Optional response format hint (e.g. ``json_object``).
            tool_choice: Optional tool choice directive (e.g. ``none``).

        Returns:
            The assistant :class:`LLMMessage`, with any tool calls parsed.
        """
        ...

    async def parse_json(self, text: str) -> Dict[str, Any]:
        """Extract/repair a JSON object from raw model output."""
        ...
