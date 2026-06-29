from typing import List, Dict, Any, Optional, Protocol
from app.domain.models.llm_message import LLMMessage


class LLM(Protocol):
    """AI service gateway interface for interacting with AI services.

    Implementations live in the infrastructure layer and own all the
    framework-specific concerns (model construction, tool binding, JSON repair
    and retry). The domain layer only deals with the framework-agnostic
    LLMMessage type.
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
            messages: Conversation history as domain LLMMessage objects.
            tools: Optional tool schemas in OpenAI function-call format.
            response_format: Optional response format type (e.g. "json_object").
            tool_choice: Optional tool choice directive (e.g. "none", "auto").

        Returns:
            The assistant LLMMessage, with any tool calls already parsed and
            repaired.
        """
        ...

    async def parse_json(self, text: str) -> dict:
        """Parse (and repair if needed) a JSON object out of model text output.

        Args:
            text: Raw text produced by the model.

        Returns:
            The parsed JSON object as a dict.
        """
        ...

    @property
    def model_name(self) -> str:
        """Get the model name"""
        ...

    @property
    def temperature(self) -> float:
        """Get the temperature"""
        ...

    @property
    def max_tokens(self) -> int:
        """Get the max tokens"""
        ...
