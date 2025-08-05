"""Gemini LLM implementation"""
import logging
from typing import List, Optional, Dict, Any

import google.generativeai as genai
from google.generativeai.types import Tool

from app.domain.external.llm import LLM
from app.infrastructure.config import get_settings

logger = logging.getLogger(__name__)

class GeminiLLM(LLM):
    """Implementation of LLM using Google's Gemini model"""

    def __init__(self):
        settings = get_settings()
        # Use the dedicated Gemini API key
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key is not configured.")
        genai.configure(api_key=settings.gemini_api_key)

        self._model_name = settings.model_name
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens
        
        generation_config = {
            "temperature": self._temperature,
            "max_output_tokens": self._max_tokens,
        }

        self._model = genai.GenerativeModel(
            self._model_name,
            generation_config=generation_config
        )
        logger.info(f"Initialized Gemini LLM with model: {self._model_name}")

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    def _convert_to_gemini_tools(self, tools: List[Dict[str, Any]]) -> List[Tool]:
        """Converts OpenAI-style tools to Gemini's Tool format."""
        if not tools:
            return []
        
        function_declarations = []
        for tool in tools:
            if tool.get("type") == "function":
                function_declarations.append(tool.get("function"))
        
        return [Tool(function_declarations=function_declarations)] if function_declarations else []

    async def ask(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None, # Note: Gemini has limited response_format support
        tool_choice: Optional[str] = None # Note: Gemini has limited tool_choice support
    ) -> Dict[str, Any]:
        """Send chat request to Gemini API"""
        
        # Convert messages to Gemini format
        gemini_messages = []
        system_prompt = None
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
                continue
            
            # Gemini expects role 'user' or 'model'
            role = "model" if msg["role"] == "assistant" else msg["role"]
            gemini_messages.append({"role": role, "parts": [msg["content"]]})

        # Prepend system message to the first user message if it exists
        if system_prompt:
            for gmsg in gemini_messages:
                if gmsg["role"] == "user":
                    gmsg["parts"][0] = f"{system_prompt}\n\n{gmsg['parts'][0]}"
                    break
        
        gemini_tools = self._convert_to_gemini_tools(tools)

        try:
            logger.debug(f"Sending request to Gemini, model: {self._model_name}")
            response = await self._model.generate_content_async(
                gemini_messages,
                tools=gemini_tools if gemini_tools else None,
            )

            first_candidate = response.candidates[0]
            part = first_candidate.content.parts[0]
            
            message = {"role": "assistant", "content": None, "tool_calls": []}

            if part.function_call:
                tool_call = {
                    "id": part.function_call.name, # Gemini doesn't provide an ID, so we use the name
                    "type": "function",
                    "function": {
                        "name": part.function_call.name,
                        "arguments": str(dict(part.function_call.args)),
                    },
                }
                message["tool_calls"].append(tool_call)
            else:
                message["content"] = part.text

            return message

        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise
