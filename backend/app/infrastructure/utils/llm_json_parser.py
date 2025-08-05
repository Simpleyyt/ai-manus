import json
import re
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import logging

from app.domain.utils.json_parser import JsonParser
from app.infrastructure.external.llm.llm_factory import create_llm


logger = logging.getLogger(__name__)

class ParseStrategy(Enum):
    """JSON parsing strategy enumeration"""
    DIRECT = "direct"
    MARKDOWN_BLOCK = "markdown_block"
    REGEX_EXTRACT = "regex_extract"
    CLEANUP_AND_PARSE = "cleanup_and_parse"
    LLM_EXTRACT_AND_FIX = "llm_extract_and_fix"


class LLMJsonParser(JsonParser):
    """
    A robust parser for converting LLM string output to JSON.
    Handles various formats including markdown code blocks, malformed JSON, etc.
    Inherits from domain JsonParser interface and uses LLM when needed.
    """
    
    def __init__(self):
        self.llm = create_llm()
        self.strategies = [
            self._try_direct_parse,
            self._try_markdown_block_parse,
            #self._try_regex_extract,
            self._try_cleanup_and_parse,
            self._try_llm_extract_and_fix,
        ]
    
    async def parse(self, text: str, default_value: Optional[Any] = None) -> Union[Dict, List, Any]:
        """
        Parse LLM output string to JSON using multiple strategies.
        Falls back to LLM parsing if local strategies fail.
        
        Args:
            text: The raw string output from LLM
            default_value: Default value to return if parsing fails
            
        Returns:
            Parsed JSON object (dict, list, or other JSON-serializable type)
            
        Raises:
            ValueError: If all parsing strategies fail and no default value provided
        """

        logger.info(f"Parsing text: {text}")
        if not text or not text.strip():
            if default_value is not None:
                return default_value
            raise ValueError("Empty input string")
        
        cleaned_output = text.strip()
        
        # Try each parsing strategy
        for strategy in self.strategies:
            try:
                result = await strategy(cleaned_output)
                if result is not None:
                    logger.info(f"Successfully parsed using strategy: {strategy.__name__}")
                    return result
            except Exception as e:
                logger.warning(f"Strategy {strategy.__name__} failed: {str(e)}")
                continue
        
        # If all strategies fail
        if default_value is not None:
            logger.warning("All parsing strategies failed, returning default value")
            return default_value
        
        raise ValueError(f"Failed to parse JSON from LLM output: {text[:1000]}...")
    
    async def _try_direct_parse(self, text: str) -> Optional[Any]:
        """Try to parse the text directly as JSON"""
        return json.loads(text)
    
    async def _try_markdown_block_parse(self, text: str) -> Optional[Any]:
        """Extract and parse JSON from markdown code blocks"""
        # Pattern to match JSON in markdown code blocks
        patterns = [
            r'```json\s*\n(.*?)\n```',
            r'```\s*\n(.*?)\n```',
            r'`([^`]*)`',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        return None
    
    async def _try_regex_extract(self, text: str) -> Optional[Any]:
        """Extract JSON using regex patterns"""
        # Look for JSON object patterns
        json_patterns = [
            r'\{.*\}',  # Object
            r'\[.*\]',  # Array
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        return None
    
    async def _try_cleanup_and_parse(self, text: str) -> Optional[Any]:
        """Clean up common formatting issues and try parsing"""
        # Remove common prefixes/suffixes
        prefixes = ["json:", "result:", "output:", "response:"]
        suffixes = [".", "..."]
        
        cleaned = text
        
        # Remove prefixes
        for prefix in prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        # Remove suffixes
        for suffix in suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        
        # Fix common JSON formatting issues
        cleaned = self._fix_json_formatting(cleaned)
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None
    
    async def _try_llm_extract_and_fix(self, text: str) -> Optional[Any]:
        """Use LLM to extract and fix JSON from the text"""
        try:
            # Run async LLM call in event loop
            result = await self._llm_extract_and_fix_async(text)
            return result
        except Exception as e:
            logger.warning(f"LLM extract and fix failed: {str(e)}")
            return None
    
    async def _llm_extract_and_fix_async(self, text: str) -> Optional[Any]:
        """Async method to use LLM for JSON extraction and fixing"""
        prompt = f"""Please extract and fix the JSON from the following text. Return only valid JSON without any explanation or markdown formatting.

Input text:
{text}

Requirements:
1. Extract any JSON-like content from the text
2. Fix common JSON formatting issues (missing quotes, trailing commas, etc.)
3. Return only the valid JSON, no additional text
4. If multiple JSON objects exist, return the most complete one
5. If no valid JSON can be extracted or fixed, return null

JSON:"""

        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = await self.llm.ask(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            content = response.get("content", "").strip()
            if content and content != "null":
                return json.loads(content)
            return None
            
        except Exception as e:
            logger.warning(f"LLM JSON extraction failed: {str(e)}")
            return None
    
    def _fix_json_formatting(self, text: str) -> str:
        """Fix common JSON formatting issues"""
        # Replace single quotes with double quotes (but not inside strings)
        # This is a simplified approach - might need more sophisticated handling
        text = re.sub(r"(?<!\\)'([^']*?)(?<!\\)'", r'"\1"', text)
        
        # Fix trailing commas
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Fix missing quotes around keys
        text = re.sub(r'(\w+):', r'"\1":', text)
        
        # Fix unescaped double quotes in string values
        # This handles cases like: "key": "value with " unescaped quotes"
        def fix_unescaped_quotes_in_values(match):
            key_part = match.group(1)  # "key": "
            value_content = match.group(2)  # value content that may contain unescaped quotes
            
            # Escape any unescaped double quotes in the value content
            # Use negative lookbehind to avoid escaping already escaped quotes
            escaped_content = re.sub(r'(?<!\\)"', r'\\"', value_content)
            
            return f'{key_part}{escaped_content}"'
        
        # Pattern to match: "key": "value content with potential " unescaped quotes"
        # Captures everything from key to the final quote of the value
        text = re.sub(r'("[\w\s\-_]+"\s*:\s*")(.*?)"(?=\s*[,}\]])', fix_unescaped_quotes_in_values, text)
        
        # Fix unescaped double quotes in array string values
        # This handles cases like: ["item with " quotes", "another item"]
        def fix_unescaped_quotes_in_array_values(match):
            quote_and_content = match.group(1)  # " + content that may contain unescaped quotes
            value_content = quote_and_content[1:]  # remove the leading quote
            
            # Escape any unescaped double quotes in the value content
            escaped_content = re.sub(r'(?<!\\)"', r'\\"', value_content)
            
            return f'"{escaped_content}"'
        
        # Pattern to match string values in arrays: "content with potential " quotes"
        # Look for quotes that are preceded by [ or , (with optional whitespace) and followed by , or ] (with optional whitespace)
        text = re.sub(r'(?<=[\[,]\s*)(".*?)"(?=\s*[,\]])', fix_unescaped_quotes_in_array_values, text)
        
        return text
