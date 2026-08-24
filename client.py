import httpx


class ScreenshotClient:
    """
    HTTP client used by the Windows agent to communicate
    with the central server.

    No global API key is used by the agent.
    """

    def __init__(
        self,
        base_url: str,
        verify_ssl: bool = False,
    ) -> None:

        self.base_url = base_url.rstrip("/")

        self.client = httpx.Client(
            base_url=self.base_url,
            verify=verify_ssl,
            timeout=30.0,
        )

    # ========================================================
    # Register agent
    # ========================================================

    def register_agent(
        self,
        agent_id: str,
    ) -> dict:

        response = self.client.post(
            "/agents/register",
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
            "/agents/heartbeat",
            json={
                "agent_id": agent_id,
            },
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # Get pending command
    # ========================================================

    def get_pending_command(
        self,
        agent_id: str,
    ) -> dict:

        response = self.client.get(
            f"/agents/{agent_id}/commands",
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # Update command status
    # ========================================================

    def update_command_status(
        self,
        agent_id: str,
        command_id: str,
        status: str,
        error: str | None = None,
    ) -> dict:

        payload = {
            "agent_id": agent_id,
            "command_id": command_id,
            "status": status,
        }

        if error is not None:
            payload["error"] = error

        response = self.client.post(
            "/commands/status",
            json=payload,
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # Upload screenshot
    # ========================================================

    def upload_screenshot(
        self,
        agent_id: str,
        command_id: str,
        image_data,
        filename: str = "screenshot.png",
    ) -> dict:

        files = {
            "file": (
                filename,
                image_data,
                "image/png",
            )
        }

        data = {
            "agent_id": agent_id,
            "command_id": command_id,
        }

        response = self.client.post(
            "/screenshots/upload",
            files=files,
            data=data,
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # Close client
    # ========================================================

    def close(self) -> None:
        self.client.close()