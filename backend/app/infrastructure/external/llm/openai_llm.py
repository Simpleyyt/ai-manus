from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.domain.external.llm import LLM
from app.infrastructure.config import get_settings
from app.application.errors.exceptions import TokenLimitExceededError
import logging
import re


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
                            response_format: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send chat request to OpenAI API"""
        logger.info("=== OpenAI LLM ask method called with TOKEN ERROR HANDLING v2.1 ===")
        response = None
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
            error_str = str(e)
            logger.error(f"=== ERROR OCCURRED IN LLM CALL ===: {error_str}")
            
            # 检查是否是token限制错误
            if any(keyword in error_str.lower() for keyword in ["token", "context", "length", "limit"]):
                
                logger.error(f"=== DETECTED TOKEN ERROR ===: {error_str}")
                
                # 直接解析token信息
                # 使用正则表达式提取大于2000的前两个数字
                numbers = re.findall(r'\b(\d{4,})\b', error_str)
                logger.error(f"=== FOUND NUMBERS ===: {numbers}")
                
                if len(numbers) >= 2:
                    # 转换为整数并排序
                    token_numbers = [int(num) for num in numbers[:2] if int(num) > 2000]
                    logger.error(f"=== FILTERED TOKEN NUMBERS ===: {token_numbers}")
                    
                    if len(token_numbers) >= 2:
                        token_numbers.sort()
                        max_tokens = token_numbers[0]  # 较小的是最大支持token数
                        current_tokens = token_numbers[1]  # 较大的是当前请求token数
                        
                        logger.error(f"=== PARSED TOKEN ERROR - Current: {current_tokens}, Max: {max_tokens} ===")
                        logger.error("=== CREATING TokenLimitExceededError ===")
                        token_error = TokenLimitExceededError(
                            msg=f"Token limit exceeded: {current_tokens}/{max_tokens}",
                            current_tokens=current_tokens,
                            max_tokens=max_tokens
                        )
                        logger.error("=== SUCCESSFULLY CREATED TokenLimitExceededError ===")
                        logger.error(f"=== TokenLimitExceededError TYPE ===: {type(token_error)}")
                        logger.error(f"=== TokenLimitExceededError ATTRS ===: current_tokens={token_error.current_tokens}, max_tokens={token_error.max_tokens}")
                        logger.error("=== RAISING TokenLimitExceededError ===")
                        raise token_error
                    else:
                        logger.error(f"=== NOT ENOUGH VALID TOKEN NUMBERS ===: {token_numbers}")
                else:
                    logger.error(f"=== NOT ENOUGH NUMBERS FOUND ===: {numbers}")
            else:
                logger.error(f"=== ERROR DOES NOT CONTAIN TOKEN KEYWORDS ===: {error_str}")
            
            logger.error("=== RE-RAISING ORIGINAL EXCEPTION ===")
            raise