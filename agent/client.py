from io import BytesIO

import httpx


class ScreenshotClient:
    """
    HTTPS client used by the agent to communicate
    with the screenshot server.
    """

    def __init__(
        self,
        server_url: str,
        api_key: str,
        verify_ssl: bool = False,
    ) -> None:

        self.server_url = (
            server_url.rstrip("/")
        )

        self.api_key = api_key

        self.client = httpx.Client(
            verify=verify_ssl,
            timeout=httpx.Timeout(
                connect=10.0,
                read=30.0,
                write=30.0,
                pool=30.0,
            ),
            headers={
                "X-API-Key": api_key,
            },
        )

    # ========================================================
    # Register Agent
    # ========================================================

    def register_agent(
        self,
        agent_id: str,
    ) -> dict:

        response = self.client.post(
            f"{self.server_url}/agents/register",
            json={
                "agent_id": agent_id,
            },
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # Heartbeat
    # ========================================================

    def send_heartbeat(
        self,
        agent_id: str,
    ) -> dict:

        response = self.client.post(
            f"{self.server_url}/agents/heartbeat",
            json={
                "agent_id": agent_id,
            },
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # Get Pending Command
    # ========================================================

    def get_pending_command(
        self,
        agent_id: str,
    ) -> dict | None:

        response = self.client.get(
            f"{self.server_url}"
            f"/agents/{agent_id}/commands",
        )

        response.raise_for_status()

        data = response.json()

        # The server may return:
        #
        # {
        #     "command": {...}
        # }
        #
        # or:
        #
        # {
        #     "command": null
        # }
        #
        # or directly return a command object.

        if isinstance(data, dict):

            if "command" in data:

                command = data.get(
                    "command"
                )

                if isinstance(
                    command,
                    dict,
                ):

                    return command

                return None

            if (
                "command_id" in data
                and "command_type" in data
            ):

                return data

        return None

    # ========================================================
    # Update Command Status
    # ========================================================

    def update_command_status(
        self,
        command_id: str,
        status: str,
        metadata: dict | None = None,
    ) -> dict:

        response = self.client.post(
            f"{self.server_url}"
            f"/agents/commands/"
            f"{command_id}/status",
            json={
                "status": status,
                "metadata": metadata,
            },
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # Upload Screenshot
    # ========================================================

    def upload_screenshot(
        self,
        image_buffer: BytesIO,
        filename: str,
        agent_id: str,
        command_id: str,
    ) -> dict:

        image_buffer.seek(0)

        response = self.client.post(
            f"{self.server_url}"
            "/screenshots/upload",
            data={
                "agent_id": agent_id,
                "command_id": command_id,
            },
            files={
                "screenshot": (
                    filename,
                    image_buffer,
                    "image/png",
                )
            },
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # Close
    # ========================================================

    def close(
        self,
    ) -> None:

        self.client.close()