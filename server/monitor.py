import threading
import time

from server.registry import AgentRegistry


class AgentStatusMonitor:
    """
    Periodically checks agent heartbeat status.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        interval: int = 30,
    ) -> None:
        self.registry = registry
        self.interval = interval

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """
        Start the monitoring thread.
        """

        self._thread = threading.Thread(
            target=self._run,
            name="AgentStatusMonitor",
            daemon=True,
        )

        self._thread.start()

    def stop(self) -> None:
        """
        Stop the monitoring thread.
        """

        self._stop_event.set()

        if self._thread is not None:
            self._thread.join()

    def _run(self) -> None:
        """
        Periodically check for stale agents.
        """

        while not self._stop_event.is_set():

            self.registry.mark_stale_agents_offline()

            self._stop_event.wait(
                self.interval
            )