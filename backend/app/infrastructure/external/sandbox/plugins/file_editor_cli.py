#!/usr/bin/env python3
"""
CLI wrapper for OpenHands file_editor
Allows calling file_editor from command line with JSON arguments
"""

import sys
import json
import os

# Add parent directory to path to import file_editor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file_editor.impl import file_editor
from file_editor.definition import FileEditorObservation


def main():
    """Main entry point for CLI"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": "Usage: file_editor_cli.py '<json_args>'"
        }))
        sys.exit(1)
    
    try:
        # Parse JSON arguments
        args_json = sys.argv[1]
        args = json.loads(args_json)
        
        # Extract command and parameters
        command = args.get("command")
        if not command:
            print(json.dumps({
                "success": False,
                "message": "Missing 'command' in arguments"
            }))
            sys.exit(1)
        
        # Call file_editor with appropriate parameters
        result: FileEditorObservation = file_editor(
            command=command,
            path=args.get("path", ""),
            file_text=args.get("file_text"),
            view_range=args.get("view_range"),
            old_str=args.get("old_str"),
            new_str=args.get("new_str"),
            insert_line=args.get("insert_line")
        )
        
        # Convert observation to JSON response
        response = {
            "success": not result.is_error if hasattr(result, 'is_error') else True,
            "message": _format_observation(result),
            "data": {
                "command": result.command if hasattr(result, 'command') else command,
                "path": result.path if hasattr(result, 'path') else args.get("path"),
                "content": _extract_content(result)
            }
        }
        
        print(json.dumps(response))
        sys.exit(0 if response["success"] else 1)
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "message": f"Error executing file_editor: {str(e)}"
        }))
        sys.exit(1)


def _format_observation(obs: FileEditorObservation) -> str:
    """Format observation into human-readable message"""
    if hasattr(obs, 'to_llm_content'):
        contents = obs.to_llm_content()
        if contents:
            # Extract text from TextContent objects
            texts = []
            for content in contents:
                if hasattr(content, 'text'):
                    texts.append(content.text)
                else:
                    texts.append(str(content))
            return "\n".join(texts)
    
    return str(obs)


def _extract_content(obs: FileEditorObservation) -> str:
    """Extract file content from observation if available"""
    if hasattr(obs, 'new_content'):
        return obs.new_content or ""
    
    # For view command, try to extract from the message
    contents = obs.to_llm_content() if hasattr(obs, 'to_llm_content') else []
    for content in contents:
        if hasattr(content, 'text'):
            return content.text
    
    return ""


if __name__ == "__main__":
    main()
