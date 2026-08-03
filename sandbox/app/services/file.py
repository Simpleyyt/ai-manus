"""
File Operation Service Implementation
"""
import os
import re
import glob
import asyncio
from typing import Optional
from fastapi import UploadFile
from app.models.file import (
    FileReadResult, FileWriteResult, FileReplaceResult,
    FileSearchResult, FileFindResult, FileUploadResult
)
from app.core.exceptions import AppException, ResourceNotFoundException, BadRequestException

# Chunk size for streaming file uploads
UPLOAD_CHUNK_SIZE = 8192


class FileService:
    """File Operation Service"""

    async def read_file(self, file: str, start_line: Optional[int] = None,
                 end_line: Optional[int] = None, sudo: bool = False, max_length: Optional[int] = 10000) -> FileReadResult:
        """
        Read file content

        Args:
            file: Absolute file path
            start_line: Starting line (0-based)
            end_line: Ending line (not included)
            sudo: Whether to use sudo privileges
            max_length: Maximum content length to return, longer content is truncated
        """
        if not os.path.exists(file) and not sudo:
            raise ResourceNotFoundException(f"File does not exist: {file}")

        try:
            if sudo:
                process = await asyncio.create_subprocess_shell(
                    f"sudo cat '{file}'",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise BadRequestException(f"Failed to read file: {stderr.decode()}")

                content = stdout.decode('utf-8')
            else:
                def read_file_content() -> str:
                    with open(file, 'r', encoding='utf-8') as f:
                        return f.read()

                # Execute IO operation in thread pool
                content = await asyncio.to_thread(read_file_content)

            # Process line range
            if start_line is not None or end_line is not None:
                lines = content.splitlines()
                start = start_line if start_line is not None else 0
                end = end_line if end_line is not None else len(lines)
                content = '\n'.join(lines[start:end])

            if max_length is not None and max_length > 0 and len(content) > max_length:
                content = content[:max_length] + "(truncated)"

            return FileReadResult(
                content=content,
                file=file
            )
        except (BadRequestException, ResourceNotFoundException):
            raise
        except Exception as e:
            raise AppException(message=f"Failed to read file: {str(e)}")

    async def write_file(self, file: str, content: str, append: bool = False,
                  leading_newline: bool = False, trailing_newline: bool = False,
                  sudo: bool = False) -> FileWriteResult:
        """
        Write file content

        Args:
            file: Absolute file path
            content: Content to write
            append: Whether to append mode
            leading_newline: Whether to add a leading newline
            trailing_newline: Whether to add a trailing newline
            sudo: Whether to use sudo privileges
        """
        try:
            if leading_newline:
                content = '\n' + content
            if trailing_newline:
                content = content + '\n'

            if sudo:
                mode = '>>' if append else '>'
                temp_file = f"/tmp/file_write_{os.getpid()}.tmp"

                def write_temp_file() -> int:
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return len(content.encode('utf-8'))

                bytes_written = await asyncio.to_thread(write_temp_file)

                # Use sudo to write temporary file content to target file
                command = f"sudo bash -c \"cat {temp_file} {mode} '{file}'\""
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise BadRequestException(f"Failed to write file: {stderr.decode()}")

                os.unlink(temp_file)
            else:
                os.makedirs(os.path.dirname(file), exist_ok=True)

                def write_file_content() -> int:
                    mode = 'a' if append else 'w'
                    with open(file, mode, encoding='utf-8') as f:
                        return f.write(content)

                bytes_written = await asyncio.to_thread(write_file_content)

            return FileWriteResult(
                file=file,
                bytes_written=bytes_written
            )
        except BadRequestException:
            raise
        except Exception as e:
            raise AppException(message=f"Failed to write file: {str(e)}")

    async def str_replace(self, file: str, old_str: str, new_str: str,
                   sudo: bool = False) -> FileReplaceResult:
        """
        Replace string in file

        Args:
            file: Absolute file path
            old_str: Original string to be replaced
            new_str: New replacement string
            sudo: Whether to use sudo privileges
        """
        file_result = await self.read_file(file, sudo=sudo)
        content = file_result.content

        replaced_count = content.count(old_str)
        if replaced_count == 0:
            return FileReplaceResult(
                file=file,
                replaced_count=0
            )

        new_content = content.replace(old_str, new_str)
        await self.write_file(file, new_content, sudo=sudo)

        return FileReplaceResult(
            file=file,
            replaced_count=replaced_count
        )

    async def find_in_content(self, file: str, regex: str,
                       sudo: bool = False) -> FileSearchResult:
        """
        Search in file content

        Args:
            file: Absolute file path
            regex: Regular expression pattern
            sudo: Whether to use sudo privileges
        """
        try:
            pattern = re.compile(regex)
        except re.error as e:
            raise BadRequestException(f"Invalid regular expression: {str(e)}")

        file_result = await self.read_file(file, sudo=sudo)
        lines = file_result.content.splitlines()

        matches = []
        line_numbers = []

        # Process in a thread pool as the file may be large
        def match_lines() -> None:
            for i, line in enumerate(lines):
                if pattern.search(line):
                    matches.append(line)
                    line_numbers.append(i)

        await asyncio.to_thread(match_lines)

        return FileSearchResult(
            file=file,
            matches=matches,
            line_numbers=line_numbers
        )

    async def find_by_name(self, path: str, glob_pattern: str) -> FileFindResult:
        """
        Find files by name pattern

        Args:
            path: Directory path to search
            glob_pattern: File name pattern (glob syntax)
        """
        if not os.path.exists(path):
            raise ResourceNotFoundException(f"Directory does not exist: {path}")

        def glob_files() -> list:
            search_pattern = os.path.join(path, glob_pattern)
            return glob.glob(search_pattern, recursive=True)

        files = await asyncio.to_thread(glob_files)

        return FileFindResult(
            path=path,
            files=files
        )

    async def upload_file(self, path: str, file_stream: UploadFile) -> FileUploadResult:
        """
        Upload file using streaming for large files

        Args:
            path: Target file path to save uploaded file
            file_stream: File stream from FastAPI UploadFile
        """
        try:
            total_size = 0

            os.makedirs(os.path.dirname(path), exist_ok=True)

            def write_stream_to_file() -> None:
                nonlocal total_size
                with open(path, 'wb') as f:
                    while True:
                        chunk = file_stream.file.read(UPLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        f.write(chunk)
                        total_size += len(chunk)

            await asyncio.to_thread(write_stream_to_file)

            return FileUploadResult(
                file_path=path,
                file_size=total_size,
                success=True
            )
        except Exception as e:
            raise AppException(message=f"Failed to upload file: {str(e)}")

    def ensure_file(self, path: str) -> None:
        """
        Ensure file exists, raising ResourceNotFoundException otherwise

        Args:
            path: Path of the file to check
        """
        if not os.path.exists(path):
            raise ResourceNotFoundException(f"File does not exist: {path}")


file_service = FileService()
