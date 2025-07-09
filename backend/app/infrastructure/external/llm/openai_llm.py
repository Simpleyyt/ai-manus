import datetime
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.domain.external.llm import LLM
from app.infrastructure.config import get_settings
import logging


logger = logging.getLogger(__name__)

# 新增日志函数
def log_llm_input(messages, tools=None, response_format=None):
    try:
        with open("/app/llm_inputs.txt", "a", encoding="utf-8") as f:
            f.write(f"\n==== {datetime.datetime.now()} ====\n")
            f.write("messages:\n")
            f.write(str(messages) + "\n")
            if tools:
                f.write("tools:\n")
                f.write(str(tools) + "\n")
            if response_format:
                f.write("response_format:\n")
                f.write(str(response_format) + "\n")
    except Exception as e:
        logger.error(f"Failed to log LLM input: {e}")


class OpenAILLM(LLM):
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.api_base
        )
        
        self._model_name = settings.model_name
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens
        logger.info(f"Initialized OpenAI LLM with model: {self._model_name}")
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def temperature(self) -> float:
        return self._temperature
    
    @property
    def max_tokens(self) -> int:
        return self._max_tokens
    
    async def ask(self, messages: List[Dict[str, str]], 
                            tools: Optional[List[Dict[str, Any]]] = None,
                            response_format: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send chat request to OpenAI API"""
        response = None
        log_llm_input(messages, tools, response_format)
        try:
            if tools:
                logger.debug(f"Sending request to OpenAI with tools, model: {self._model_name}")
                response = await self.client.chat.completions.create(
                    model=self._model_name,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    messages=messages,
                    tools=tools,
                    response_format=response_format,
                )
            else:
                logger.debug(f"Sending request to OpenAI without tools, model: {self._model_name}")
                response = await self.client.chat.completions.create(
                    model=self._model_name,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    messages=messages,
                    response_format=response_format
                )
            return response.choices[0].message.model_dump()
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise