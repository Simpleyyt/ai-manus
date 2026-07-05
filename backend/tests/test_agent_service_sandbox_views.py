"""Application-layer tests for sandbox view use cases (mocked sandbox)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.sandbox import FileViewDto, ShellViewDto
from app.application.services.agent_service import AgentService
from app.domain.models.session import Session
from app.domain.models.tool_result import ToolResult


def _make_agent_service(
    session: Session,
    sandbox: AsyncMock,
) -> AgentService:
    session_repository = AsyncMock()
    session_repository.find_by_id_and_user_id.return_value = session

    sandbox_cls = MagicMock()
    sandbox_cls.get = AsyncMock(return_value=sandbox)

    return AgentService(
        agent_repository=AsyncMock(),
        session_repository=session_repository,
        sandbox_cls=sandbox_cls,
        task_cls=MagicMock(),
        file_storage=AsyncMock(),
        mcp_repository=AsyncMock(),
        llm=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_shell_view_returns_dto_from_sandbox_result():
    session = Session(agent_id="a1", user_id="u1", sandbox_id="sb-1")
    sandbox = AsyncMock()
    sandbox.view_shell.return_value = ToolResult(
        success=True,
        data={
            "output": "hello world",
            "session_id": "shell-42",
            "console": [{"ps1": "$", "command": "echo hi", "output": "hi\n"}],
        },
    )
    service = _make_agent_service(session, sandbox)

    dto = await service.shell_view("sess-1", "shell-42", "u1")

    assert isinstance(dto, ShellViewDto)
    assert dto.output == "hello world"
    assert dto.session_id == "shell-42"
    assert dto.console[0].command == "echo hi"
    sandbox.view_shell.assert_awaited_once_with("shell-42", console=True)


@pytest.mark.asyncio
async def test_file_view_returns_dto_from_sandbox_result():
    session = Session(agent_id="a1", user_id="u1", sandbox_id="sb-1")
    sandbox = AsyncMock()
    sandbox.file_read.return_value = ToolResult(
        success=True,
        data={"content": "file body", "file": "/tmp/demo.txt"},
    )
    service = _make_agent_service(session, sandbox)

    dto = await service.file_view("sess-1", "/tmp/demo.txt", "u1")

    assert isinstance(dto, FileViewDto)
    assert dto.content == "file body"
    assert dto.file == "/tmp/demo.txt"
    sandbox.file_read.assert_awaited_once_with("/tmp/demo.txt")


@pytest.mark.asyncio
async def test_shell_view_raises_when_sandbox_call_fails():
    session = Session(agent_id="a1", user_id="u1", sandbox_id="sb-1")
    sandbox = AsyncMock()
    sandbox.view_shell.return_value = ToolResult(success=False, message="shell gone")
    service = _make_agent_service(session, sandbox)

    with pytest.raises(RuntimeError, match="Failed to get shell output"):
        await service.shell_view("sess-1", "shell-42", "u1")
