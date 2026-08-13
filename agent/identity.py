import json
from pathlib import Path
from uuid import uuid4


class AgentIdentity:
    """
    Manages the persistent identity of the agent.
    """

    def __init__(
        self,
        identity_file: Path,
    ) -> None:
        self.identity_file = identity_file
        self.agent_id = self._load_or_create_identity()

    def get_agent_id(self) -> str:
        """
        Return the persistent agent ID.
        """

        return self.agent_id

    def _load_or_create_identity(self) -> str:
        """
        Load an existing agent ID or create a new one.
        """

        if self.identity_file.exists():
            return self._load_identity()

        agent_id = str(uuid4())

        self._save_identity(
            agent_id
        )

        return agent_id

    def _load_identity(self) -> str:
        """
        Load the agent ID from the identity file.
        """

        with self.identity_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return data["agent_id"]

    def _save_identity(
        self,
        agent_id: str,
    ) -> None:
        """
        Save the agent ID to disk.
        """

        self.identity_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.identity_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                {
                    "agent_id": agent_id,
                },
                file,
                indent=4,
            )