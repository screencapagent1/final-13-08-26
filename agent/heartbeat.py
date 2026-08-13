import threading


class HeartbeatWorker:
    """
    Sends periodic heartbeat messages to the server.
    """

    def __init__(
        self,
        client,
        agent_id: str,
        interval: int = 180,
    ) -> None:

        self.client = client
        self.agent_id = agent_id
        self.interval = interval

        self._stop_event = threading.Event()

        self._thread: (
            threading.Thread
            | None
        ) = None

    def start(
        self,
    ) -> None:

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):

            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="HeartbeatWorker",
            daemon=True,
        )

        self._thread.start()

    def stop(
        self,
    ) -> None:

        self._stop_event.set()

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):

            self._thread.join(
                timeout=self.interval + 2
            )

        print(
            "Heartbeat worker stopped."
        )

    def _run(
        self,
    ) -> None:

        while not self._stop_event.is_set():

            try:

                self.client.send_heartbeat(
                    self.agent_id
                )

                print(
                    "Heartbeat sent successfully."
                )

            except Exception as error:

                print(
                    "Heartbeat error:"
                )

                print(
                    repr(error)
                )

            self._stop_event.wait(
                self.interval
            )