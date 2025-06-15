from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import yaml
from typing import List, Optional, Dict, Any
import os
from pathlib import Path
import asyncio
import logging
import sys

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    #id: str
    #object: str
    #created: int
    #model: str
    choices: List[Dict[str, Any]]

def load_mock_data():
    # Get mock data filename from environment variable, default to default.yaml
    mock_file = os.getenv("MOCK_DATA_FILE", "default.yaml")
    mock_file_path = Path(__file__).parent / "mock_datas" / mock_file

    with open(mock_file_path, 'r', encoding='utf-8') as f:
        logger.info(f"Loading mock data from {mock_file}")
        if mock_file.endswith('.json'):
            return json.load(f)
        else:
            return yaml.safe_load(f)

current_index = 0

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    global current_index
    mock_data = load_mock_data()
    if not mock_data:
        current_index = 0
        logger.error("No mock data available")
        raise HTTPException(status_code=500, detail="No mock data available")
    
    delay = float(os.getenv("MOCK_DELAY", "1"))
    if delay > 0:
        logger.debug(f"Applying mock delay of {delay} seconds")
        await asyncio.sleep(delay)
    
    response = mock_data[current_index]
    current_index = (current_index + 1) % len(mock_data)
    logger.info(f"Returning mock response {current_index}/{len(mock_data)}")
    return response
