import os
import sys
import time
from pathlib import Path

from agent.client import ScreenshotClient
from agent.command_worker import CommandWorker
from agent.heartbeat import HeartbeatWorker
from agent.identity import AgentIdentity
from agent.screen_capture import ScreenCapture


# ============================================================
# Application directory
# ============================================================

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# Configuration
# ============================================================

SERVER_URL = (
    "https://192.168.32.1:8443"
)


# ============================================================
# Main Application
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # Load persistent agent identity
    # --------------------------------------------------------

    identity = AgentIdentity(
        identity_file=(
            APP_DIR
            / "agent"
            / "data"
            / "agent_identity.json"
        )
    )

    agent_id = (
        identity.get_agent_id()
    )

    print(
        f"Starting agent: "
        f"{agent_id}"
    )


    # --------------------------------------------------------
    # Create HTTPS client
    # --------------------------------------------------------

    client = ScreenshotClient(

        base_url=SERVER_URL,

        verify_ssl=False,

    )


    # --------------------------------------------------------
    # Create screenshot capture object
    # --------------------------------------------------------

    screen_capture = (
        ScreenCapture()
    )


    heartbeat = None

    command_worker = None


    # ========================================================
    # Command Handler
    # ========================================================

    def handle_command(
        command: dict,
    ) -> None:

        command_type = (
            command.get(
                "command_type"
            )
        )

        command_id = (
            command.get(
                "command_id"
            )
        )


        print(
            "Received command: "
            f"{command_type}"
        )


        print(
            "Command ID: "
            f"{command_id}"
        )


        # ----------------------------------------------------
        # Validate command
        # ----------------------------------------------------

        if (
            command_type
            != "capture_screenshot"
        ):

            print(
                "Unknown command type."
            )

            return


        try:

            # ------------------------------------------------
            # Capture screenshot
            # ------------------------------------------------

            print(
                "Capturing screenshot..."
            )


            image_buffer = (
                screen_capture
                .capture_png()
            )


            screenshot_size = len(
                image_buffer.getvalue()
            )


            print(
                "Screenshot captured "
                "successfully."
            )


            print(
                f"Screenshot size: "
                f"{screenshot_size} "
                "bytes"
            )


            # ------------------------------------------------
            # Generate filename
            # ------------------------------------------------

            filename = (
                f"{agent_id}_"
                f"{command_id}.png"
            )


            # ------------------------------------------------
            # Upload screenshot
            # ------------------------------------------------

            print(
                "Uploading screenshot..."
            )


            result = (
                client
                .upload_screenshot(

                    image_buffer=image_buffer,

                    filename=filename,

                    agent_id=agent_id,

                    command_id=command_id,

                )
            )


            print(
                "Screenshot uploaded "
                "successfully."
            )


            print(
                "Upload result:"
            )


            print(
                result
            )


        except Exception as error:

            print(
                "Screenshot processing "
                "failed:"
            )


            print(
                error
            )


    # ========================================================
    # Start Agent
    # ========================================================

    try:

        # ----------------------------------------------------
        # Register agent
        # ----------------------------------------------------

        while True:

            try:

                client.register_agent(
                    agent_id
                )

                print(
                    "Agent registered "
                    "successfully."
                )

                break

            except Exception as error:

                print(
                    "Unable to connect to server."
                )

                print(
                    f"Registration error: {error}"
                )

                print(
                    "Retrying in 10 seconds..."
                )

                time.sleep(10)


        # ----------------------------------------------------
        # Start heartbeat worker
        # ----------------------------------------------------

        heartbeat = (
            HeartbeatWorker(

                client=client,

                agent_id=agent_id,

                interval=3 * 60,

            )
        )


        heartbeat.start()


        print(
            "Heartbeat worker started."
        )


        # ----------------------------------------------------
        # Start command worker
        # ----------------------------------------------------

        command_worker = (
            CommandWorker(

                client=client,

                agent_id=agent_id,

                interval=5,

                command_handler=(
                    handle_command
                ),

            )
        )


        command_worker.start()


        print(
            "Command worker started."
        )


        # ----------------------------------------------------
        # Keep agent alive
        # ----------------------------------------------------

        while True:

            time.sleep(
                1
            )


    except KeyboardInterrupt:

        print(
            "Stopping agent..."
        )


    finally:

        # ----------------------------------------------------
        # Stop command worker
        # ----------------------------------------------------

        if (
            command_worker
            is not None
        ):

            command_worker.stop()


        # ----------------------------------------------------
        # Stop heartbeat worker
        # ----------------------------------------------------

        if (
            heartbeat
            is not None
        ):

            heartbeat.stop()


        # ----------------------------------------------------
        # Close HTTP client
        # ----------------------------------------------------

        client.close()


        print(
            "Agent stopped."
        )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    main()