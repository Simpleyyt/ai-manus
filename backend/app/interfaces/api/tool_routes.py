from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/tools", tags=["tools"])

class ToolParameter(BaseModel):
    name: str
    type: str
    required: bool
    description: str
    actions: Optional[List[str]] = None
    nested_properties: Optional[List['ToolParameter']] = None

class Tool(BaseModel):
    name: str
    category: str
    purpose: str
    instructions: List[str]
    parameters: List[ToolParameter]
    examples: Optional[List[str]] = None

class ToolCategory(BaseModel):
    name: str
    description: str
    tools: List[Tool]

# Built-in Manus Tools Data
BUILTIN_TOOLS = [
    ToolCategory(
        name="Core Tools",
        description="Always available tools invoked via function calling",
        tools=[
            Tool(
                name="plan",
                category="Core Tools",
                purpose="Create, update, and advance the structured task plan",
                instructions=[
                    "MUST update the task plan when user makes new requests or changes requirements",
                    "Phase count scales with task complexity: simple (2), typical (4-6), complex (10+)",
                    "When confident a phase is complete, MUST advance using the advance action",
                    "next_phase_id MUST be the next sequential ID after current_phase_id",
                    "Skipping phases or going backward is NOT allowed"
                ],
                parameters=[
                    ToolParameter(name="action", type="STRING", required=True, description="The action to perform: update or advance", actions=["update", "advance"]),
                    ToolParameter(name="current_phase_id", type="INTEGER", required=True, description="ID of the phase the task is currently in", actions=["update", "advance"]),
                    ToolParameter(name="goal", type="STRING", required=False, description="The overall goal of the task", actions=["update"]),
                    ToolParameter(name="next_phase_id", type="INTEGER", required=False, description="ID of the phase the task is advancing to", actions=["advance"]),
                    ToolParameter(
                        name="phases",
                        type="ARRAY",
                        required=False,
                        description="Complete list of phases required to achieve the task goal",
                        actions=["update"],
                        nested_properties=[
                            ToolParameter(name="id", type="INTEGER", required=True, description="Auto-incrementing phase ID"),
                            ToolParameter(name="title", type="STRING", required=True, description="Concise human-readable title of the phase"),
                            ToolParameter(name="capabilities", type="OBJECT", required=True, description="Specific capabilities required for this phase")
                        ]
                    )
                ],
                examples=[
                    "plan(action='update', current_phase_id=1, goal='Research and write a report', phases=[...])",
                    "plan(action='advance', current_phase_id=1, next_phase_id=2)"
                ]
            ),
            Tool(
                name="message",
                category="Core Tools",
                purpose="Send messages to interact with the user, deliver results, and manage the task lifecycle",
                instructions=[
                    "MUST use this tool for any communication with users",
                    "The first reply MUST be a brief acknowledgment without providing solutions",
                    "Use info for progress updates",
                    "Use ask only when a user response is required",
                    "MUST use result to present final results and end the task",
                    "MUST attach all relevant files in attachments",
                    "NEVER deliver intermediate notes as the only result"
                ],
                parameters=[
                    ToolParameter(name="type", type="STRING", required=True, description="The type of the message: info, ask, result", actions=["info", "ask", "result"]),
                    ToolParameter(name="text", type="STRING", required=True, description="The message or question text to be shown to the user"),
                    ToolParameter(name="attachments", type="ARRAY", required=False, description="A list of absolute file paths or URLs to attach"),
                    ToolParameter(name="suggested_action", type="STRING", required=False, description="The suggested action for the user to take", actions=["ask"])
                ]
            ),
            Tool(
                name="shell",
                category="Core Tools",
                purpose="Interact with shell sessions in the sandbox environment for command execution, file management, and process control",
                instructions=[
                    "Prioritize file tool for file content operations",
                    "MUST avoid commands that require confirmation; use flags like -y or -f",
                    "Chain multiple commands with && to reduce interruptions",
                    "NEVER run code directly via interpreter commands; MUST save code to a file first",
                    "Use wait after exec for long-running commands",
                    "Use \\n at the end of input for the send action to simulate Enter"
                ],
                parameters=[
                    ToolParameter(name="action", type="STRING", required=True, description="The action to perform: view, exec, wait, send, kill"),
                    ToolParameter(name="session", type="STRING", required=True, description="The unique identifier of the target shell session"),
                    ToolParameter(name="brief", type="STRING", required=True, description="A one-sentence preamble describing the purpose of this operation"),
                    ToolParameter(name="command", type="STRING", required=False, description="The shell command to execute", actions=["exec"]),
                    ToolParameter(name="input", type="STRING", required=False, description="Input text to send to the interactive session", actions=["send"]),
                    ToolParameter(name="timeout", type="INTEGER", required=False, description="Timeout in seconds. Defaults to 30s", actions=["exec", "wait"])
                ]
            ),
            Tool(
                name="file",
                category="Core Tools",
                purpose="Perform operations on file content in the sandbox file system",
                instructions=[
                    "view is for multimodal understanding (images, PDFs)",
                    "read is for text-based content (code, Markdown)",
                    "DO NOT use range when reading a file for the first time",
                    "write and append automatically create files if they do not exist",
                    "edit can make multiple targeted edits at once"
                ],
                parameters=[
                    ToolParameter(name="action", type="STRING", required=True, description="The action to perform: view, read, write, append, edit"),
                    ToolParameter(name="path", type="STRING", required=True, description="The absolute path to the target file"),
                    ToolParameter(name="brief", type="STRING", required=True, description="A one-sentence preamble describing the purpose of this operation"),
                    ToolParameter(name="range", type="ARRAY", required=False, description="Start and end of the range (1-indexed)", actions=["view", "read"]),
                    ToolParameter(name="text", type="STRING", required=False, description="The content to be written or appended", actions=["write", "append"]),
                    ToolParameter(
                        name="edits",
                        type="ARRAY",
                        required=False,
                        description="A list of edits to be sequentially applied",
                        actions=["edit"],
                        nested_properties=[
                            ToolParameter(name="find", type="STRING", required=True, description="The exact text string to find in the file"),
                            ToolParameter(name="replace", type="STRING", required=True, description="The replacement text that will substitute the found text"),
                            ToolParameter(name="all", type="BOOLEAN", required=False, description="Whether to replace all occurrences instead of just the first one")
                        ]
                    )
                ]
            ),
            Tool(
                name="search",
                category="Core Tools",
                purpose="Search for up-to-date or external information across various sources",
                instructions=[
                    "MUST use this tool to access up-to-date or external information",
                    "DO NOT rely solely on search result snippets; MUST follow up by navigating to source URLs using browser",
                    "Each search may contain up to 3 queries, which MUST be variants of the same intent",
                    "For complex searches, break down into step-by-step searches"
                ],
                parameters=[
                    ToolParameter(name="type", type="STRING", required=True, description="The category of search: info, image, api, news, tool, data, research"),
                    ToolParameter(name="brief", type="STRING", required=True, description="A one-sentence preamble describing the purpose of this operation"),
                    ToolParameter(name="queries", type="ARRAY", required=True, description="Up to 3 query variants that express the same search intent"),
                    ToolParameter(name="time", type="STRING", required=False, description="Optional time filter: all, past_day, past_week, past_month, past_year")
                ]
            ),
            Tool(
                name="browser",
                category="Core Tools",
                purpose="Navigate the browser to a specified URL to begin a web browsing session and unlock nested browser tools",
                instructions=[
                    "MUST use this tool to start browser interactions",
                    "MUST access multiple URLs from search results for comprehensive information",
                    "The browser maintains login state across tasks"
                ],
                parameters=[
                    ToolParameter(name="brief", type="STRING", required=True, description="A one-sentence preamble describing the purpose of this operation"),
                    ToolParameter(name="url", type="STRING", required=True, description="The URL to navigate to. Must include protocol prefix"),
                    ToolParameter(name="intent", type="STRING", required=True, description="The purpose of visiting: navigational, informational, transactional"),
                    ToolParameter(name="focus", type="STRING", required=False, description="Specific topic, section, or question to focus on")
                ]
            ),
            Tool(
                name="generate",
                category="Core Tools",
                purpose="Enter generation mode to create or edit images, videos, audio, and speech from text and media references",
                instructions=[
                    "Use for creating visual, audio, or speech content",
                    "After calling, the agent gains access to tools like generate_image, generate_audio, etc."
                ],
                parameters=[
                    ToolParameter(name="brief", type="STRING", required=True, description="A one-sentence preamble describing the purpose of this operation")
                ]
            )
        ]
    )
]

@router.get("/", response_model=List[ToolCategory])
async def get_all_tools():
    """Get all available tools organized by category"""
    return BUILTIN_TOOLS

@router.get("/categories", response_model=List[str])
async def get_tool_categories():
    """Get list of all tool categories"""
    return [category.name for category in BUILTIN_TOOLS]

@router.get("/category/{category_name}", response_model=ToolCategory)
async def get_tools_by_category(category_name: str):
    """Get all tools in a specific category"""
    for category in BUILTIN_TOOLS:
        if category.name.lower() == category_name.lower():
            return category
    raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")

@router.get("/tool/{tool_name}", response_model=Tool)
async def get_tool_by_name(tool_name: str):
    """Get detailed information about a specific tool"""
    for category in BUILTIN_TOOLS:
        for tool in category.tools:
            if tool.name.lower() == tool_name.lower():
                return tool
    raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

@router.get("/search")
async def search_tools(q: str):
    """Search for tools by name, purpose, or instructions"""
    results = []
    query = q.lower()
    
    for category in BUILTIN_TOOLS:
        for tool in category.tools:
            if (query in tool.name.lower() or 
                query in tool.purpose.lower() or 
                any(query in instruction.lower() for instruction in tool.instructions)):
                results.append(tool)
    
    return results
