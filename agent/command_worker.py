import threading
import time
from typing import Callable
import httpx

class CommandWorker:
    """
    Continuously polls the server for commands.

    The worker runs in a background thread so that
    it does not block the main agent process.
    """

    def __init__(
        self,
        client,
        agent_id: str,
        interval: int = 5,
        command_handler: Callable[
            [dict],
            None,
        ] | None = None,
    ) -> None:

        self.client = client

        self.agent_id = agent_id

        self.interval = interval

        self.command_handler = (
            command_handler
        )

        self._stop_event = (
            threading.Event()
        )

        self._thread: (
            threading.Thread
            | None
        ) = None

    def start(
        self,
    ) -> None:
        """
        Start the command worker.
        """

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):

            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="CommandWorker",
            daemon=True,
        )

        self._thread.start()

    def stop(
        self,
    ) -> None:
        """
        Stop the command worker.
        """

        self._stop_event.set()

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):

            self._thread.join(
                timeout=self.interval + 2
            )

        print(
            "Command worker stopped."
        )

    def _run(
        self,
    ) -> None:
        """
        Poll the server continuously.
        """

        while not self._stop_event.is_set():

            try:

                command = self.client.get_pending_command(
                    self.agent_id
                )

                if command is not None:

                    print("Command received:")

                    print(command)

                    if self.command_handler is not None:

                        self.command_handler(command)

            except httpx.HTTPStatusError as error:

                print("Command worker HTTP error:")

                print(repr(error))

                # ----------------------------------------------------
                # Server restarted and forgot this agent
                # ----------------------------------------------------

                if error.response.status_code == 404:

                    try:

                        print(
                            "Agent is not registered "
                            "on the server."
                        )

                        print("Re-registering agent...")

                        self.client.register_agent(self.agent_id)

                        print(
                            "Agent re-registered "
                            "successfully."
                        )

                    except Exception as register_error:

                        print("Agent re-registration failed:")

                        print(repr(register_error))

                        time.sleep(5)

                else:

                    time.sleep(1)

            except Exception as error:

                print("Command worker error:")

                print(repr(error))

                # Prevent rapid retry loops
                # if the server connection
                # temporarily fails.

                time.sleep(1)

            self._stop_event.wait(self.interval)