"""
Shell Service Implementation
"""
import os
import uuid
import getpass
import socket
import logging
import asyncio
import re
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from app.models.shell import (
    ShellExecResult, ShellViewResult, ShellWaitResult,
    ShellWriteResult, ShellKillResult, ConsoleRecord
)
from app.core.exceptions import AppException, ResourceNotFoundException, BadRequestException

logger = logging.getLogger(__name__)

# Pattern to match ANSI escape sequences
ANSI_ESCAPE_PATTERN = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# How long exec_command waits for a command before reporting it as still running
EXEC_WAIT_SECONDS = 5
# Default timeout for wait_for_process when none is given
DEFAULT_WAIT_SECONDS = 60
# Default maximum length of output returned to clients, longer output is truncated
DEFAULT_OUTPUT_MAX_LENGTH = 10000
# Maximum output kept in memory per session, older output is discarded
MAX_STORED_OUTPUT_LENGTH = 1024 * 1024


@dataclass
class ShellSession:
    """State of a single shell session"""
    process: asyncio.subprocess.Process
    exec_dir: str
    output: str = ""
    console: List[ConsoleRecord] = field(default_factory=list)


class ShellService:
    def __init__(self) -> None:
        self.active_shells: Dict[str, ShellSession] = {}

    def create_session_id(self) -> str:
        """Create a new session ID"""
        session_id = str(uuid.uuid4())
        logger.debug(f"Created new session ID: {session_id}")
        return session_id

    def _get_session(self, session_id: str) -> ShellSession:
        """Get an existing session or raise ResourceNotFoundException"""
        session = self.active_shells.get(session_id)
        if session is None:
            logger.error(f"Session ID not found: {session_id}")
            raise ResourceNotFoundException(f"Session ID does not exist: {session_id}")
        return session

    @staticmethod
    def _remove_ansi_escape_codes(text: str) -> str:
        """Remove ANSI escape codes from text"""
        return ANSI_ESCAPE_PATTERN.sub('', text)

    @staticmethod
    def _truncate_output(text: str, max_length: Optional[int]) -> str:
        """Truncate output to max_length, keeping the most recent (tail) part"""
        if max_length is not None and max_length > 0 and len(text) > max_length:
            return "(truncated)" + text[-max_length:]
        return text

    @staticmethod
    def _append_bounded(stored: str, new_output: str) -> str:
        """Append new output to stored output, discarding the oldest part beyond the memory cap"""
        stored += new_output
        # Allow some slack before trimming to avoid copying the string on every append
        if len(stored) > MAX_STORED_OUTPUT_LENGTH + 64 * 1024:
            stored = stored[-MAX_STORED_OUTPUT_LENGTH:]
        return stored

    @staticmethod
    def _get_display_path(path: str) -> str:
        """Get the path for display, replacing user home directory with ~"""
        home_dir = os.path.expanduser("~")
        if path.startswith(home_dir):
            return path.replace(home_dir, "~", 1)
        return path

    def _format_ps1(self, exec_dir: str) -> str:
        """Format the command prompt"""
        username = getpass.getuser()
        hostname = socket.gethostname()
        display_dir = self._get_display_path(exec_dir)
        return f"{username}@{hostname}:{display_dir} $"

    async def _create_process(self, command: str, exec_dir: str) -> asyncio.subprocess.Process:
        """Create a new async subprocess"""
        logger.debug(f"Creating process for command: {command} in directory: {exec_dir}")
        return await asyncio.create_subprocess_shell(
            command,
            executable="/bin/bash",
            cwd=exec_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Redirect stderr to stdout
            stdin=asyncio.subprocess.PIPE,
            limit=1024 * 1024  # Set buffer size to 1MB
        )

    async def _terminate_process(self, process: asyncio.subprocess.Process, timeout: float) -> None:
        """Terminate a process gracefully, force killing it if it does not exit in time"""
        if process.returncode is not None:
            return
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=timeout)
        except (asyncio.TimeoutError, ProcessLookupError):
            logger.warning("Graceful termination failed, force killing process")
            process.kill()
            await process.wait()

    async def _read_output(self, session_id: str, process: asyncio.subprocess.Process) -> None:
        """Continuously read process output and append it to the session state"""
        logger.debug(f"Starting output reader for session: {session_id}")
        while process.stdout:
            try:
                buffer = await process.stdout.read(128)
            except Exception as e:
                logger.error(f"Error reading process output: {str(e)}", exc_info=True)
                break
            if not buffer:
                break  # Process output ended

            output = buffer.decode('utf-8')
            session = self.active_shells.get(session_id)
            # Only record output if this process is still the session's current one
            if session and session.process is process:
                session.output = self._append_bounded(session.output, output)
                if session.console:
                    record = session.console[-1]
                    record.output = self._append_bounded(record.output, output)
        logger.debug(f"Output reader for session {session_id} has finished")

    async def exec_command(self, session_id: str, exec_dir: Optional[str], command: str) -> ShellExecResult:
        """
        Execute a command in the specified shell session.

        Creates the session if it does not exist yet; if the session already has a
        running process, that process is terminated first. Waits briefly for the
        command to complete; returns a "running" result if it is still going.
        """
        logger.info(f"Executing command in session {session_id}: {command}")
        if not exec_dir:
            exec_dir = os.path.expanduser("~")
        if not os.path.exists(exec_dir):
            logger.error(f"Directory does not exist: {exec_dir}")
            raise BadRequestException(f"Directory does not exist: {exec_dir}")

        try:
            session = self.active_shells.get(session_id)
            if session is not None and session.process.returncode is None:
                logger.debug(f"Terminating previous process in session: {session_id}")
                await self._terminate_process(session.process, timeout=1)

            process = await self._create_process(command, exec_dir)
            record = ConsoleRecord(ps1=self._format_ps1(exec_dir), command=command, output="")

            if session is None:
                logger.debug(f"Creating new shell session: {session_id}")
                self.active_shells[session_id] = ShellSession(
                    process=process,
                    exec_dir=exec_dir,
                    console=[record],
                )
            else:
                logger.debug(f"Reusing existing shell session: {session_id}")
                session.process = process
                session.exec_dir = exec_dir
                session.output = ""  # Clear previous output
                session.console.append(record)

            asyncio.create_task(self._read_output(session_id, process))
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}", exc_info=True)
            raise AppException(
                message=f"Command execution failed: {str(e)}",
                data={"session_id": session_id, "command": command}
            )

        try:
            wait_result = await self.wait_for_process(session_id, seconds=EXEC_WAIT_SECONDS)
        except BadRequestException:
            # Wait timeout, process still running
            logger.debug(f"Process still running after timeout in session: {session_id}")
            return ShellExecResult(
                session_id=session_id,
                command=command,
                status="running",
            )

        logger.debug(f"Process completed with code: {wait_result.returncode}")
        view_result = await self.view_shell(session_id)
        return ShellExecResult(
            session_id=session_id,
            command=command,
            status="completed",
            returncode=wait_result.returncode,
            output=view_result.output,
        )

    async def view_shell(self, session_id: str, console: bool = False,
                         max_length: Optional[int] = DEFAULT_OUTPUT_MAX_LENGTH) -> ShellViewResult:
        """
        View the output of the specified shell session.

        Output longer than max_length is truncated, keeping the most recent part.
        """
        logger.debug(f"Viewing shell content for session: {session_id}")
        session = self._get_session(session_id)
        return ShellViewResult(
            output=self._truncate_output(self._remove_ansi_escape_codes(session.output), max_length),
            session_id=session_id,
            console=self.get_console_records(session_id, max_length) if console else None,
        )

    def get_console_records(self, session_id: str,
                            max_length: Optional[int] = DEFAULT_OUTPUT_MAX_LENGTH) -> List[ConsoleRecord]:
        """Get console records for the specified session, with ANSI escape codes removed and output truncated"""
        logger.debug(f"Getting console records for session: {session_id}")
        session = self._get_session(session_id)
        return [
            ConsoleRecord(
                ps1=record.ps1,
                command=record.command,
                output=self._truncate_output(self._remove_ansi_escape_codes(record.output), max_length),
            )
            for record in session.console
        ]

    async def wait_for_process(self, session_id: str, seconds: Optional[int] = None) -> ShellWaitResult:
        """Wait for the process in the specified shell session to return"""
        logger.debug(f"Waiting for process in session: {session_id}, timeout: {seconds}s")
        session = self._get_session(session_id)
        if seconds is None:
            seconds = DEFAULT_WAIT_SECONDS

        try:
            await asyncio.wait_for(session.process.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            logger.warning(f"Process wait timeout expired: {seconds}s")
            raise BadRequestException(f"Wait timeout: {seconds} seconds")
        except Exception as e:
            logger.error(f"Failed to wait for process: {str(e)}", exc_info=True)
            raise AppException(message=f"Failed to wait for process: {str(e)}")

        logger.info(f"Process completed with return code: {session.process.returncode}")
        return ShellWaitResult(returncode=session.process.returncode)

    async def write_to_process(self, session_id: str, input_text: str, press_enter: bool) -> ShellWriteResult:
        """Write input to the process in the specified shell session"""
        logger.debug(f"Writing to process in session: {session_id}, press_enter: {press_enter}")
        session = self._get_session(session_id)
        process = session.process

        if process.returncode is not None:
            logger.error("Process has already terminated, cannot write input")
            raise BadRequestException("Process has ended, cannot write input")

        try:
            input_str = f"{input_text}\n" if press_enter else input_text

            # Echo the input into the session output and console records
            session.output += input_str
            if session.console:
                session.console[-1].output += input_str

            process.stdin.write(input_str.encode())
            await process.stdin.drain()

            logger.info("Successfully wrote input to process")
            return ShellWriteResult(status="success")
        except Exception as e:
            logger.error(f"Failed to write input: {str(e)}", exc_info=True)
            raise AppException(message=f"Failed to write input: {str(e)}")

    async def kill_process(self, session_id: str) -> ShellKillResult:
        """Terminate the process in the specified shell session"""
        logger.info(f"Killing process in session: {session_id}")
        session = self._get_session(session_id)
        process = session.process

        if process.returncode is not None:
            logger.info(f"Process was already terminated with return code: {process.returncode}")
            return ShellKillResult(
                status="already_terminated",
                returncode=process.returncode
            )

        try:
            await self._terminate_process(process, timeout=3)
            logger.info(f"Process terminated with return code: {process.returncode}")
            return ShellKillResult(
                status="terminated",
                returncode=process.returncode
            )
        except Exception as e:
            logger.error(f"Failed to kill process: {str(e)}", exc_info=True)
            raise AppException(message=f"Failed to terminate process: {str(e)}")


shell_service = ShellService()
