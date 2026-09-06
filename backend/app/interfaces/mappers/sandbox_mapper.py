from app.application.dto.sandbox import FileViewDto, ShellViewDto
from app.interfaces.schemas.file import FileViewResponse
from app.interfaces.schemas.session import ConsoleRecord, ShellViewResponse


def to_shell_view_response(dto: ShellViewDto) -> ShellViewResponse:
    console = None
    if dto.console is not None:
        console = [
            ConsoleRecord(ps1=record.ps1, command=record.command, output=record.output)
            for record in dto.console
        ]
    return ShellViewResponse(
        output=dto.output,
        session_id=dto.session_id,
        console=console,
    )


def to_file_view_response(dto: FileViewDto) -> FileViewResponse:
    return FileViewResponse(content=dto.content, file=dto.file)
