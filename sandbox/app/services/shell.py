"""
Shell Service Implementation - Async Version
"""
import os
import subprocess
import uuid
import getpass
import socket
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from app.models.shell import (
    ShellCommandResult, ShellViewResult, ShellWaitResult,
    ShellWriteResult, ShellKillResult, ShellTask, ConsoleRecord
)
from app.core.exceptions import AppException, ResourceNotFoundException, BadRequestException

# Set up logger
logger = logging.getLogger(__name__)

class ShellService:
    # Store active shell sessions
    active_shells: Dict[str, Dict[str, Any]] = {}
    
    # Store shell tasks
    shell_tasks: Dict[str, ShellTask] = {}

    def _get_display_path(self, path: str) -> str:
        """Get the path for display, replacing user home directory with ~"""
        home_dir = os.path.expanduser("~")
        logger.debug(f"Home directory: {home_dir} , path: {path}")
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
            cwd=exec_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Redirect stderr to stdout
            stdin=asyncio.subprocess.PIPE,
            limit=1024*1024  # Set buffer size to 1MB
        )

    async def _start_output_reader(self, session_id: str, process: asyncio.subprocess.Process):
        """Start a coroutine to continuously read process output and store it"""
        logger.debug(f"Starting output reader for session: {session_id}")
        while True:
            if process.stdout:
                try:
                    buffer = await process.stdout.read(128)
                    if not buffer:
                        # Process output ended
                        break
                    
                    output = buffer.decode('utf-8')
                    # Add output to shell session
                    shell = self.active_shells.get(session_id)
                    if shell:
                        shell["output"] += output
                        # Update the output of the latest console record
                        if shell["console"]:
                            shell["console"][-1].output += output
                except Exception as e:
                    logger.error(f"Error reading process output: {str(e)}", exc_info=True)
                    break
            else:
                break
        
        logger.debug(f"Output reader for session {session_id} has finished")

    async def exec_command(self, session_id: str, exec_dir: Optional[str], command: str) -> ShellCommandResult:
        """
        Asynchronously execute a command in the specified shell session
        """
        logger.info(f"Executing command in session {session_id}: {command}")
        if not exec_dir:
            exec_dir = os.path.expanduser("~")
        # Ensure directory exists
        if not os.path.exists(exec_dir):
            logger.error(f"Directory does not exist: {exec_dir}")
            raise BadRequestException(f"Directory does not exist: {exec_dir}")
        
        try:
            # Create PS1 format
            ps1 = self._format_ps1(exec_dir)
            
            # If it's a new session, create a new process
            if session_id not in self.active_shells:
                logger.debug(f"Creating new shell session: {session_id}")
                process = await self._create_process(command, exec_dir)
                self.active_shells[session_id] = {
                    "process": process,
                    "exec_dir": exec_dir,
                    "output": "",
                    "console": [ConsoleRecord(ps1=ps1, command=command, output="")]
                }
                # Start the output reader coroutine
                asyncio.create_task(self._start_output_reader(session_id, process))
            else:
                # Execute command in an existing session
                logger.debug(f"Using existing shell session: {session_id}")
                shell = self.active_shells[session_id]
                old_process = shell["process"]
                
                # If the old process is still running, terminate it first
                if old_process.returncode is None:
                    logger.debug(f"Terminating previous process in session: {session_id}")
                    try:
                        old_process.terminate()
                        await asyncio.wait_for(old_process.wait(), timeout=1)
                    except:
                        # If graceful termination fails, force kill
                        logger.warning(f"Forcefully killing process in session: {session_id}")
                        old_process.kill()
                
                # Create a new process
                process = await self._create_process(command, exec_dir)
                
                # Update session information
                self.active_shells[session_id]["process"] = process
                self.active_shells[session_id]["exec_dir"] = exec_dir
                self.active_shells[session_id]["output"] = ""  # Clear previous output
                
                # Record command console record, but output is initially empty, will be updated later
                shell["console"].append(ConsoleRecord(ps1=ps1, command=command, output=""))
                
                # Start the output reader coroutine
                asyncio.create_task(self._start_output_reader(session_id, process))
            
            # Try to wait for the process to complete (max 5 seconds)
            try:
                logger.debug(f"Waiting for process completion in session: {session_id}")
                wait_result = await self.wait_for_process(session_id, seconds=5)
                if wait_result.returncode is not None:
                    # Process has completed, get the output
                    logger.debug(f"Process completed with code: {wait_result.returncode}")
                    view_result = await self.view_shell(session_id)
                    # Update the output of the latest console record
                    if self.active_shells[session_id]["console"]:
                        self.active_shells[session_id]["console"][-1].output = view_result.output
                    
                    # Get command console records
                    console = self.get_console_records(session_id)
                    
                    return ShellCommandResult(
                        session_id=session_id,
                        command=command,
                        status="completed",
                        returncode=wait_result.returncode,
                        output=view_result.output,
                        console=console
                    )
            except BadRequestException:
                # Wait timeout, process still running
                logger.debug(f"Process still running after timeout in session: {session_id}")
                pass
            except Exception as e:
                # Other exceptions, ignore and continue
                logger.warning(f"Exception while waiting for process: {str(e)}")
                pass
            
            # Get current console records
            console = self.get_console_records(session_id)
            
            return ShellCommandResult(
                session_id=session_id,
                command=command,
                status="running",
                console=console
            )
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}", exc_info=True)
            raise AppException(
                message=f"Command execution failed: {str(e)}",
                data={"session_id": session_id, "command": command}
            )

    async def view_shell(self, session_id: str) -> ShellViewResult:
        """
        Asynchronously view the content of the specified shell session
        """
        logger.debug(f"Viewing shell content for session: {session_id}")
        if session_id not in self.active_shells:
            logger.error(f"Session ID not found: {session_id}")
            raise ResourceNotFoundException(f"Session ID does not exist: {session_id}")
        
        shell = self.active_shells[session_id]
        
        # Directly use the stored output
        output = shell["output"]
        
        # Get command console records
        console = self.get_console_records(session_id)
        
        return ShellViewResult(
            output=output,
            session_id=session_id,
            console=console
        )

    def get_console_records(self, session_id: str) -> List[ConsoleRecord]:
        """
        Get command console records for the specified session (this method doesn't need to be async)
        """
        logger.debug(f"Getting console records for session: {session_id}")
        if session_id not in self.active_shells:
            logger.error(f"Session ID not found: {session_id}")
            raise ResourceNotFoundException(f"Session ID does not exist: {session_id}")
        
        return self.active_shells[session_id]["console"]

    async def wait_for_process(self, session_id: str, seconds: Optional[int] = None) -> ShellWaitResult:
        """
        Asynchronously wait for the process in the specified shell session to return
        """
        logger.debug(f"Waiting for process in session: {session_id}, timeout: {seconds}s")
        if session_id not in self.active_shells:
            logger.error(f"Session ID not found: {session_id}")
            raise ResourceNotFoundException(f"Session ID does not exist: {session_id}")
        
        shell = self.active_shells[session_id]
        process = shell["process"]
        
        try:
            # Asynchronously wait for process to complete
            if seconds is None:
                seconds = 60
            await asyncio.wait_for(process.wait(), timeout=seconds)
            
            logger.info(f"Process completed with return code: {process.returncode}")
            return ShellWaitResult(
                returncode=process.returncode
            )
        except asyncio.TimeoutError:
            logger.warning(f"Process wait timeout expired: {seconds}s")
            raise BadRequestException(f"Wait timeout: {seconds} seconds")
        except Exception as e:
            logger.error(f"Failed to wait for process: {str(e)}", exc_info=True)
            raise AppException(message=f"Failed to wait for process: {str(e)}")

    async def write_to_process(self, session_id: str, input_text: str, press_enter: bool) -> ShellWriteResult:
        """
        Asynchronously write input to the process in the specified shell session
        """
        logger.debug(f"Writing to process in session: {session_id}, press_enter: {press_enter}")
        if session_id not in self.active_shells:
            logger.error(f"Session ID not found: {session_id}")
            raise ResourceNotFoundException(f"Session ID does not exist: {session_id}")
        
        shell = self.active_shells[session_id]
        process = shell["process"]
        
        try:
            # Check if the process is still running
            if process.returncode is not None:
                logger.error(f"Process has already terminated, cannot write input")
                raise BadRequestException("Process has ended, cannot write input")
            
            # Prepare input data
            if press_enter:
                input_data = f"{input_text}\n".encode()
            else:
                input_data = input_text.encode()
            
            # Add input to output and console records
            input_str = input_data.decode('utf-8')
            shell["output"] += input_str
            if shell["console"]:
                shell["console"][-1].output += input_str
            
            # Asynchronously write input
            process.stdin.write(input_data)
            await process.stdin.drain()
            
            logger.info(f"Successfully wrote input to process")
            
            return ShellWriteResult(
                status="success"
            )
        except Exception as e:
            logger.error(f"Failed to write input: {str(e)}", exc_info=True)
            raise AppException(message=f"Failed to write input: {str(e)}")

    async def kill_process(self, session_id: str) -> ShellKillResult:
        """
        Asynchronously terminate the process in the specified shell session
        """
        logger.info(f"Killing process in session: {session_id}")
        if session_id not in self.active_shells:
            logger.error(f"Session ID not found: {session_id}")
            raise ResourceNotFoundException(f"Session ID does not exist: {session_id}")
        
        shell = self.active_shells[session_id]
        process = shell["process"]
        
        try:
            # Check if the process is still running
            if process.returncode is None:
                # Try to terminate gracefully
                logger.debug(f"Attempting to terminate process gracefully")
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=3)
                except asyncio.TimeoutError:
                    # If graceful termination fails, force kill
                    logger.warning(f"Forcefully killing the process")
                    process.kill()
                    await process.wait()
                
                logger.info(f"Process terminated with return code: {process.returncode}")
                return ShellKillResult(
                    status="terminated",
                    returncode=process.returncode
                )
            else:
                logger.info(f"Process was already terminated with return code: {process.returncode}")
                return ShellKillResult(
                    status="already_terminated",
                    returncode=process.returncode
                )
        except Exception as e:
            logger.error(f"Failed to kill process: {str(e)}", exc_info=True)
            raise AppException(message=f"Failed to terminate process: {str(e)}")

    def create_session_id(self) -> str:
        """
        Create a new session ID (this method doesn't need to be async)
        """
        session_id = str(uuid.uuid4())
        logger.debug(f"Created new session ID: {session_id}")
        return session_id

shell_service = ShellService()