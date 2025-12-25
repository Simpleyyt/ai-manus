from typing import Optional, Dict, Any
from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult
from app.infrastructure.loggers import logger
import os
import json

class FileTool(BaseTool):
    """File tool class using OpenHands SDK file_editor
    
    Enhanced with:
    - OpenHands SDK file_editor for advanced editing capabilities
    - Excel/CSV analysis using pandas
    - PDF text and table extraction
    - Smart file detection and processing
    - Stateful session support
    """

    name: str = "file"
    
    def __init__(self, sandbox: Sandbox):
        """Initialize file tool class
        
        Args:
            sandbox: Sandbox service
        """
        super().__init__()
        self.sandbox = sandbox
        
    @tool(
        name="file_view",
        description="View file content with line numbers. Perfect for reading code, configs, or logs. Uses OpenHands file_editor for consistent behavior.",
        parameters={
            "path": {
                "type": "string",
                "description": "Absolute or relative path of the file to view"
            },
            "view_range": {
                "type": "array",
                "description": "(Optional) [start_line, end_line] 1-indexed. Example: [1, 50] views lines 1-50",
                "items": {"type": "integer"}
            }
        },
        required=["path"]
    )
    async def file_view(
        self,
        path: str,
        view_range: Optional[list] = None
    ) -> ToolResult:
        """View file content using OpenHands file_editor
        
        Args:
            path: Absolute or relative path of the file
            view_range: Optional [start_line, end_line] 1-indexed
            
        Returns:
            File content with line numbers
        """
        try:
            # Build command arguments
            args = {
                "command": "view",
                "path": path
            }
            if view_range:
                args["view_range"] = view_range
            
            # Execute file_editor inside sandbox
            cmd = f"python3 /openhands/tools/file_editor_cli.py '{json.dumps(args)}'"
            result = await self.sandbox.exec_command_stateful(
                command=cmd,
                session_id="default"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"file_view failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"Failed to view file: {str(e)}"
            )
    
    @tool(
        name="file_create",
        description="Create a new file with content. Uses OpenHands file_editor for robust file creation.",
        parameters={
            "path": {
                "type": "string",
                "description": "Absolute or relative path of the file to create"
            },
            "file_text": {
                "type": "string",
                "description": "Complete content to write to the file"
            }
        },
        required=["path", "file_text"]
    )
    async def file_create(
        self,
        path: str,
        file_text: str
    ) -> ToolResult:
        """Create a new file using OpenHands file_editor
        
        Args:
            path: Path of the file to create
            file_text: Content to write
            
        Returns:
            Creation result
        """
        try:
            args = {
                "command": "create",
                "path": path,
                "file_text": file_text
            }
            
            cmd = f"python3 /openhands/tools/file_editor_cli.py '{json.dumps(args)}'"
            result = await self.sandbox.exec_command_stateful(
                command=cmd,
                session_id="default"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"file_create failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"Failed to create file: {str(e)}"
            )
    
    @tool(
        name="file_str_replace",
        description="Replace string in a file intelligently. Uses OpenHands file_editor for smart string replacement with context awareness.",
        parameters={
            "path": {
                "type": "string",
                "description": "Absolute or relative path of the file"
            },
            "old_str": {
                "type": "string",
                "description": "Exact string to find and replace (must match exactly including whitespace)"
            },
            "new_str": {
                "type": "string",
                "description": "New string to replace with"
            }
        },
        required=["path", "old_str", "new_str"]
    )
    async def file_str_replace(
        self,
        path: str,
        old_str: str,
        new_str: str
    ) -> ToolResult:
        """Replace string in file using OpenHands file_editor
        
        Args:
            path: Path of the file
            old_str: Original string to replace
            new_str: New string
            
        Returns:
            Replacement result
        """
        try:
            args = {
                "command": "str_replace",
                "path": path,
                "old_str": old_str,
                "new_str": new_str
            }
            
            cmd = f"python3 /openhands/tools/file_editor_cli.py '{json.dumps(args)}'"
            result = await self.sandbox.exec_command_stateful(
                command=cmd,
                session_id="default"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"file_str_replace failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"Failed to replace string: {str(e)}"
            )
    
    @tool(
        name="file_find_in_content",
        description="Search for matching text within file content. Use for finding specific content or patterns in files.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the file to search within"
            },
            "regex": {
                "type": "string",
                "description": "Regular expression pattern to match"
            },
            "sudo": {
                "type": "boolean",
                "description": "(Optional) Whether to use sudo privileges"
            }
        },
        required=["file", "regex"]
    )
    async def file_find_in_content(
        self,
        file: str,
        regex: str,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Search for matching text in file content
        
        Args:
            file: Absolute path of the file to search
            regex: Regular expression pattern for matching
            sudo: (Optional) Whether to use sudo privileges
            
        Returns:
            Search results
        """
        # Directly call sandbox's file_search method
        return await self.sandbox.file_search(
            file=file,
            regex=regex,
            sudo=sudo
        )
    
    @tool(
        name="file_find_by_name",
        description="Find files by name pattern in specified directory. Use for locating files with specific naming patterns.",
        parameters={
            "path": {
                "type": "string",
                "description": "Absolute path of directory to search"
            },
            "glob": {
                "type": "string",
                "description": "Filename pattern using glob syntax wildcards"
            }
        },
        required=["path", "glob"]
    )
    async def file_find_by_name(
        self,
        path: str,
        glob: str
    ) -> ToolResult:
        """Find files by name pattern in specified directory
        
        Args:
            path: Absolute path of directory to search
            glob: Filename pattern using glob syntax wildcards
            
        Returns:
            Search results
        """
        # Directly call sandbox's file_find method
        return await self.sandbox.file_find(
            path=path,
            glob_pattern=glob
        )
    
    @tool(
        name="file_analyze_excel",
        description="Analyze Excel or CSV file with pandas. Supports data queries like 'get average of column X' or 'count rows where Y > 100'.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the Excel (.xlsx, .xls) or CSV file"
            },
            "query": {
                "type": "string",
                "description": "(Optional) Analysis query: 'average column_name', 'sum column_name', 'count', 'max', 'min', 'unique values'"
            }
        },
        required=["file"]
    )
    async def file_analyze_excel(
        self,
        file: str,
        query: Optional[str] = None
    ) -> ToolResult:
        """Analyze Excel or CSV file using pandas
        
        Args:
            file: Absolute path of Excel/CSV file
            query: Optional analysis query
            
        Returns:
            File analysis with statistics and query results
        """
        try:
            # Import the processor
            from app.domain.services.tools.file_processors import DataFileProcessor
            
            # Get file extension
            _, ext = os.path.splitext(file)
            
            # Download file as binary directly (no redundant file_read)
            try:
                file_stream = await self.sandbox.file_download(file)
                file_content = file_stream.read()
            except Exception as e:
                # Security: Don't leak internal exception details to user
                logger.error(f"Excel/CSV download failed for {file}: {str(e)}")
                return ToolResult(
                    success=False,
                    message="Failed to download file for processing. Please check the file path and try again."
                )
            
            # Process with pandas
            analysis_result = DataFileProcessor.process_excel_csv(
                file_content=file_content,
                file_extension=ext,
                query=query
            )
            
            if not analysis_result.get("success"):
                return ToolResult(
                    success=False,
                    message=analysis_result.get("error", "Analysis failed")
                )
            
            # Format result message
            summary = analysis_result["summary"]
            message = f"Excel/CSV Analysis:\n"
            message += f"- Rows: {summary['rows']}\n"
            message += f"- Columns: {summary['columns']}\n"
            message += f"- Column names: {', '.join(summary['column_names'])}\n"
            
            if analysis_result.get("query_result"):
                query_res = analysis_result["query_result"]
                if query_res.get("result"):
                    message += f"\nQuery Result: {query_res['result']}"
                elif query_res.get("error"):
                    message += f"\nQuery Error: {query_res['error']}"
            
            return ToolResult(
                success=True,
                message=message,
                data=analysis_result
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to analyze file: {str(e)}"
            )
    
    @tool(
        name="file_extract_pdf",
        description="Extract text and tables from PDF files. Maintains document structure and extracts tables in structured format.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the PDF file"
            },
            "extract_tables": {
                "type": "boolean",
                "description": "(Optional) Whether to extract tables. Default is True."
            },
            "start_page": {
                "type": "integer",
                "description": "(Optional) Starting page number (0-indexed)"
            },
            "end_page": {
                "type": "integer",
                "description": "(Optional) Ending page number (exclusive)"
            }
        },
        required=["file"]
    )
    async def file_extract_pdf(
        self,
        file: str,
        extract_tables: Optional[bool] = True,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None
    ) -> ToolResult:
        """Extract text and tables from PDF file
        
        Args:
            file: Absolute path of PDF file
            extract_tables: Whether to extract tables
            start_page: Optional starting page
            end_page: Optional ending page
            
        Returns:
            Extracted text and tables
        """
        try:
            # Import the processor
            from app.domain.services.tools.file_processors import PDFProcessor
            
            # Download file from sandbox
            try:
                file_stream = await self.sandbox.file_download(file)
                file_content = file_stream.read()
            except Exception as e:
                # Security: Don't leak internal exception details to user
                logger.error(f"PDF download failed for {file}: {str(e)}")
                return ToolResult(
                    success=False,
                    message="Failed to download PDF file. Please check the file path and try again."
                )
            
            # Prepare page range - handle both start and end together, or individually
            page_range = None
            if start_page is not None or end_page is not None:
                # Validation: Ensure non-negative page numbers
                if start_page is not None and start_page < 0:
                    return ToolResult(
                        success=False,
                        message="Invalid start_page: must be non-negative (0-indexed)"
                    )
                
                if end_page is not None and end_page < 0:
                    return ToolResult(
                        success=False,
                        message="Invalid end_page: must be non-negative"
                    )
                
                # Validation: start must be less than end if both provided
                if start_page is not None and end_page is not None:
                    if start_page >= end_page:
                        return ToolResult(
                            success=False,
                            message=f"Invalid page range: start_page ({start_page}) must be less than end_page ({end_page})"
                        )
                
                # If only one is provided, use it with a default for the other
                start = start_page if start_page is not None else 0
                # end will be set to total pages in the processor if None
                page_range = (start, end_page)
            
            # Process PDF
            extraction_result = PDFProcessor.process_pdf(
                file_content=file_content,
                extract_tables=extract_tables,
                page_range=page_range
            )
            
            if not extraction_result.get("success"):
                return ToolResult(
                    success=False,
                    message=extraction_result.get("error", "PDF extraction failed")
                )
            
            # Format result message
            message = f"PDF Extraction:\n"
            message += f"- Total pages: {extraction_result['total_pages']}\n"
            message += f"- Pages processed: {len(extraction_result['pages'])}\n"
            message += f"- Tables found: {len(extraction_result['tables'])}\n"
            message += f"\nExtracted text preview:\n{extraction_result['text'][:500]}..."
            
            return ToolResult(
                success=True,
                message=message,
                data=extraction_result
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to extract PDF: {str(e)}"
            ) 