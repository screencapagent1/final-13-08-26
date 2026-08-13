from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from uuid import uuid4


class CommandType(str, Enum):
    CAPTURE_SCREENSHOT = "capture_screenshot"


class CommandStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CAPTURING = "capturing"
    CAPTURED = "captured"
    UPLOADED = "uploaded"
    FAILED = "failed"


@dataclass
class Command:
    command_id: str
    agent_id: str
    command_type: CommandType
    status: CommandStatus
    created_at: datetime

    completed_at: datetime | None = None
    error: str | None = None
    filename: str | None = None
    size_bytes: int | None = None

    def to_dict(self) -> dict:

        return {

            "command_id":
            self.command_id,

            "agent_id":
            self.agent_id,

            "command_type":
            self.command_type.value,

            "status":
            self.status.value,

            "created_at":
            self.created_at.isoformat(),

            "completed_at":
            (
                self.completed_at.isoformat()
                if self.completed_at
                else None
            ),

            "error":
            self.error,

            "filename":
            self.filename,

            "size_bytes":
            self.size_bytes,

        }


class CommandManager:

    def __init__(self) -> None:

        self._commands: dict[
            str,
            Command
        ] = {}

        self._lock = Lock()

    # ========================================================
    # Create screenshot command
    # ========================================================

    def create_screenshot_command(
        self,
        agent_id: str,
    ) -> Command:

        command = Command(

            command_id=str(
                uuid4()
            ),

            agent_id=agent_id,

            command_type=(
                CommandType
                .CAPTURE_SCREENSHOT
            ),

            status=(
                CommandStatus
                .PENDING
            ),

            created_at=(
                datetime.now(
                    timezone.utc
                )
            ),

        )

        with self._lock:

            self._commands[
                command.command_id
            ] = command

        return command

    # ========================================================
    # Get pending command
    # ========================================================

    def get_pending_command(
        self,
        agent_id: str,
    ) -> Command | None:

        with self._lock:

            for command in (
                self._commands.values()
            ):

                if (

                    command.agent_id
                    == agent_id

                    and

                    command.status
                    == CommandStatus.PENDING

                ):

                    command.status = (

                        CommandStatus
                        .IN_PROGRESS

                    )

                    return command

        return None

    # ========================================================
    # Get command
    # ========================================================

    def get_command(
        self,
        command_id: str,
    ) -> Command | None:

        with self._lock:

            return self._commands.get(
                command_id
            )

    # ========================================================
    # Update command status
    # ========================================================

    def update_status(
        self,
        command_id: str,
        status: str,
        metadata: dict | None = None,
    ) -> bool:

        with self._lock:

            command = self._commands.get(
                command_id
            )

            if command is None:

                return False

            try:

                new_status = (
                    CommandStatus(
                        status
                    )
                )

            except ValueError:

                return False

            command.status = new_status

            if metadata:

                if "filename" in metadata:

                    command.filename = (
                        metadata[
                            "filename"
                        ]
                    )

                if "size_bytes" in metadata:

                    try:

                        command.size_bytes = (
                            int(
                                metadata[
                                    "size_bytes"
                                ]
                            )
                        )

                    except (
                        TypeError,
                        ValueError,
                    ):

                        pass

                if "error" in metadata:

                    command.error = (
                        metadata[
                            "error"
                        ]
                    )

            if new_status in (

                CommandStatus
                .UPLOADED,

                CommandStatus
                .FAILED,

            ):

                command.completed_at = (

                    datetime.now(
                        timezone.utc
                    )

                )

            return True

    # ========================================================
    # Complete command
    # ========================================================

    def complete_command(
        self,
        command_id: str,
        filename: str,
        size_bytes: int,
    ) -> bool:

        with self._lock:

            command = self._commands.get(
                command_id
            )

            if command is None:

                return False

            command.status = (

                CommandStatus
                .UPLOADED

            )

            command.completed_at = (

                datetime.now(
                    timezone.utc
                )

            )

            command.filename = (
                filename
            )

            command.size_bytes = (
                size_bytes
            )

            return True

    # ========================================================
    # Fail command
    # ========================================================

    def fail_command(
        self,
        command_id: str,
        error: str,
    ) -> bool:

        with self._lock:

            command = self._commands.get(
                command_id
            )

            if command is None:

                return False

            command.status = (

                CommandStatus
                .FAILED

            )

            command.error = (
                error
            )

            command.completed_at = (

                datetime.now(
                    timezone.utc
                )

            )

            return True

    # ========================================================
    # Convert command to dictionary
    # ========================================================

    @staticmethod
    def command_to_dict(
        command: Command,
    ) -> dict:

        return command.to_dict()