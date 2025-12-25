import os
import subprocess
import time

from openhands.sdk.utils.truncate import maybe_truncate
from openhands.tools.file_editor.utils.constants import (
    CONTENT_TRUNCATED_NOTICE,
    MAX_RESPONSE_LEN_CHAR,
)


def run_shell_cmd(
    cmd: str,
    timeout: float | None = 120.0,  # seconds
    truncate_after: int | None = MAX_RESPONSE_LEN_CHAR,
    truncate_notice: str = CONTENT_TRUNCATED_NOTICE,
) -> tuple[int, str, str]:
    """Run a shell command synchronously with a timeout.

    Args:
        cmd: The shell command to run.
        timeout: The maximum time to wait for the command to complete.
        truncate_after: The maximum number of characters to return for stdout
            and stderr.

    Returns:
        A tuple containing the return code, stdout, and stderr.
    """

    start_time = time.time()

    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        stdout, stderr = process.communicate(timeout=timeout)

        return (
            process.returncode or 0,
            maybe_truncate(
                stdout, truncate_after=truncate_after, truncate_notice=truncate_notice
            ),
            maybe_truncate(
                stderr,
                truncate_after=truncate_after,
                truncate_notice=CONTENT_TRUNCATED_NOTICE,
            ),  # Use generic notice for stderr
        )
    except subprocess.TimeoutExpired:
        if process:
            process.kill()
        elapsed_time = time.time() - start_time
        raise TimeoutError(
            f"Command '{cmd}' timed out after {elapsed_time:.2f} seconds"
        )


def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            check=True,
            cwd=os.getcwd(),
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
