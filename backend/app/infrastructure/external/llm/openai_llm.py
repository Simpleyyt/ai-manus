from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.domain.external.llm import LLM
from app.core.config import get_settings
import logging
import asyncio
import time
from collections.abc import AsyncIterator


logger = logging.getLogger(__name__)

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
                response_format: Optional[Dict[str, Any]] = None,
                tool_choice: Optional[str] = None) -> Dict[str, Any]:
        """Send chat request to OpenAI API with retry mechanism"""
        max_retries = 3
        base_delay = 1.0  

        for attempt in range(max_retries + 1):  # every try
            response = None
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))  # back off
                    logger.info(f"Retrying OpenAI API request (attempt {attempt + 1}/{max_retries + 1}) after {delay}s delay")
                    await asyncio.sleep(delay)

                if tools:
                    logger.debug(f"Sending request to OpenAI with tools, model: {self._model_name}, attempt: {attempt + 1}")
                    response = await self.client.chat.completions.create(
                        model=self._model_name,
                        temperature=self._temperature,
                        max_tokens=self._max_tokens,
                        messages=messages,
                        tools=tools,
                        response_format=response_format,
                        tool_choice=tool_choice,
                        parallel_tool_calls=False,
                    )
                else:
                    logger.debug(f"Sending request to OpenAI without tools, model: {self._model_name}, attempt: {attempt + 1}")
                    response = await self.client.chat.completions.create(
                        model=self._model_name,
                        temperature=self._temperature,
                        max_tokens=self._max_tokens,
                        messages=messages,
                        response_format=response_format,
                    )

                logger.debug(f"Response from OpenAI: {response.model_dump()}")

                
                if not response or not response.choices:
                    error_msg = f"OpenAI API returned invalid response (no choices) on attempt {attempt + 1}"
                    logger.error(error_msg)
                    if attempt == max_retries:
                        raise ValueError(f"Failed after {max_retries + 1} attempts: {error_msg}")
                    continue

                return response.choices[0].message.model_dump()

            except Exception as e:
                error_msg = f"Error calling OpenAI API on attempt {attempt + 1}: {str(e)}"
                logger.error(error_msg)
                if attempt == max_retries:
                    raise e
                continue


    async def ask_stream(
            self,
            messages: List[Dict[str, str]],
            tools: Optional[List[Dict[str, Any]]] = None,
            response_format: Optional[Dict[str, Any]] = None,
            tool_choice: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        try:
            # 构建基础参数
            params = {
                "model": self._model_name,
                "temperature": self._temperature,
                "max_tokens": self._max_tokens,
                "messages": messages,
                "stream": True,  # 关键：启用流式
            }

            # 如果有 tools，添加相关参数
            if tools:
                logger.debug(f"Sending streaming request to OpenAI with tools, model: {self._model_name}")
                params.update({
                    "tools": tools,
                    "response_format": response_format,
                    "tool_choice": tool_choice,
                    "parallel_tool_calls": False,
                })
            else:
                logger.debug(f"Sending streaming request to OpenAI without tools, model: {self._model_name}")
                if response_format:
                    params["response_format"] = response_format
            # 调用流式 API
            stream = await self.client.chat.completions.create(**params)
            # 迭代流式响应
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta = choice.delta.model_dump()
                    # TODO: reasoning_content 显示
                    if ("content" in delta and delta["content"]) \
                        or ("tool_calls" in delta and delta["tool_calls"]):
                        yield delta
                    else:
                        # TODO: 其他逻辑
                        continue
                else:
                    logging.info(f"Done: {chunk.model_dump()}")
                    break
        except Exception as e:
            logger.error(f"Error calling OpenAI streaming API: {str(e)}")
            raise
