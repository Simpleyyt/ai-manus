"""Unit tests for application DTOs and sandbox mappers."""

import pytest
from pydantic import ValidationError

from app.application.dto.sandbox import ConsoleRecordDto, FileViewDto, ShellViewDto
from app.domain.models.sandbox.file import FileReadResult
from app.domain.models.sandbox.shell import ShellViewResult
from app.interfaces.mappers.sandbox_mapper import to_file_view_response, to_shell_view_response


class TestShellViewDto:
    def test_from_result_with_console(self):
        domain = ShellViewResult(
            output="hello",
            session_id="shell-1",
            console=[
                {"ps1": "$", "command": "ls", "output": "a.txt"},
            ],
        )
        dto = ShellViewDto.from_result(domain)

        assert dto.output == "hello"
        assert dto.session_id == "shell-1"
        assert len(dto.console) == 1
        assert isinstance(dto.console[0], ConsoleRecordDto)
        assert dto.console[0].command == "ls"

    def test_from_result_without_console(self):
        domain = ShellViewResult(output="x", session_id="shell-2")
        dto = ShellViewDto.from_result(domain)

        assert dto.console is None

    def test_from_domain_model_validate_wire_payload(self):
        raw = {
            "output": "hi",
            "session_id": "s1",
            "console": [{"ps1": "#", "command": "pwd", "output": "/tmp"}],
            "extra_field": "ignored",
        }
        domain = ShellViewResult.model_validate(raw)
        dto = ShellViewDto.from_result(domain)

        assert dto.output == "hi"
        assert dto.console[0].output == "/tmp"

    def test_domain_model_rejects_missing_required_fields(self):
        with pytest.raises(ValidationError):
            ShellViewResult.model_validate({"output": "only-output"})


class TestFileViewDto:
    def test_from_result(self):
        domain = FileReadResult(content="print('hi')", file="/workspace/main.py")
        dto = FileViewDto.from_result(domain)

        assert dto.content == "print('hi')"
        assert dto.file == "/workspace/main.py"


class TestSandboxMapper:
    def test_to_shell_view_response(self):
        dto = ShellViewDto(
            output="out",
            session_id="sid",
            console=[ConsoleRecordDto(ps1="$", command="echo hi", output="hi\n")],
        )
        response = to_shell_view_response(dto)

        assert response.output == "out"
        assert response.session_id == "sid"
        assert response.console[0].command == "echo hi"

    def test_to_file_view_response(self):
        dto = FileViewDto(content="body", file="/etc/hosts")
        response = to_file_view_response(dto)

        assert response.content == "body"
        assert response.file == "/etc/hosts"

    def test_end_to_end_shell_wire_to_api_schema(self):
        wire = {
            "output": "done",
            "session_id": "wire-1",
            "console": [{"ps1": ">", "command": "date", "output": "2026"}],
        }
        dto = ShellViewDto.from_result(ShellViewResult.model_validate(wire))
        api = to_shell_view_response(dto)

        assert api.output == "done"
        assert api.console[0].output == "2026"
