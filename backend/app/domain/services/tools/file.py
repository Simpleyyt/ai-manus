from typing import Optional, Dict, Any
from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.base import BaseToolkit
from app.domain.models.tool_result import ToolResult
from langchain.tools import tool

class FileToolkit(BaseToolkit):
    """File tool class, providing file operation functions"""

    name: str = "file"
    
    def __init__(self, sandbox: Sandbox):
        """Initialize file tool class
        
        Args:
            sandbox: Sandbox service
        """
        super().__init__()
        self.sandbox = sandbox
        
    @tool(parse_docstring=True)
    async def file_read(
        self,
        file: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Read file content. Use for checking file contents, analyzing logs, or reading configuration files.
        
        Args:
            file: Absolute path of the file to read
            start_line: (Optional) Starting line to read from, 0-based
            end_line: (Optional) Ending line number (exclusive)
            sudo: (Optional) Whether to use sudo privileges
        """
        # Directly call sandbox's file_read method
        return await self.sandbox.file_read(
            file=file,
            start_line=start_line,
            end_line=end_line,
            sudo=sudo
        )
    
    @tool(parse_docstring=True)
    async def file_write(
        self,
        file: str,
        content: str,
        append: Optional[bool] = False,
        leading_newline: Optional[bool] = False,
        trailing_newline: Optional[bool] = False,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Overwrite or append content to a file. Use for creating new files, appending content, or modifying existing files.
        
        Args:
            file: Absolute path of the file to write to
            content: Text content to write
            append: (Optional) Whether to use append mode
            leading_newline: (Optional) Whether to add a leading newline
            trailing_newline: (Optional) Whether to add a trailing newline
            sudo: (Optional) Whether to use sudo privileges
        """
        # Prepare content
        final_content = content
        if leading_newline:
            final_content = "\n" + final_content
        if trailing_newline:
            final_content = final_content + "\n"
            
        # Directly call sandbox's file_write method, pass all parameters
        return await self.sandbox.file_write(
            file=file, 
            content=final_content,
            append=append,
            leading_newline=False,  # Already handled in final_content
            trailing_newline=False,  # Already handled in final_content
            sudo=sudo
        )
    
    @tool(parse_docstring=True)
    async def file_str_replace(
        self,
        file: str,
        old_str: str,
        new_str: str,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Replace specified string in a file. Use for updating specific content in files or fixing errors in code.
        
        Args:
            file: Absolute path of the file to perform replacement on
            old_str: Original string to be replaced
            new_str: New string to replace with
            sudo: (Optional) Whether to use sudo privileges
        """
        # Directly call sandbox's file_replace method
        return await self.sandbox.file_replace(
            file=file,
            old_str=old_str,
            new_str=new_str,
            sudo=sudo
        )
    
    @tool(parse_docstring=True)
    async def file_find_in_content(
        self,
        file: str,
        regex: str,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Search for matching text within file content. Use for finding specific content or patterns in files.
        
        Args:
            file: Absolute path of the file to search within
            regex: Regular expression pattern to match
            sudo: (Optional) Whether to use sudo privileges
        """
        # Directly call sandbox's file_search method
        return await self.sandbox.file_search(
            file=file,
            regex=regex,
            sudo=sudo
        )
    
    @tool(parse_docstring=True)
    async def file_find_by_name(
        self,
        path: str,
        glob: str
    ) -> ToolResult:
        """Find files by name pattern in specified directory. Use for locating files with specific naming patterns.
        
        Args:
            path: Absolute path of directory to search
            glob: Filename pattern using glob syntax wildcards
        """
        # Directly call sandbox's file_find method
        return await self.sandbox.file_find(
            path=path,
            glob_pattern=glob
        ) 