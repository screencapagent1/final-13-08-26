from datetime import datetime, timedelta, timezone
from threading import Lock


class AgentRegistry:
    """
    Maintains information about registered agents.
    """

    def __init__(
        self,
        offline_threshold_seconds: int = 90,
    ) -> None:

        self._agents: dict[
            str,
            dict[str, str],
        ] = {}

        self._offline_threshold = timedelta(
            seconds=offline_threshold_seconds
        )

        self._lock = Lock()

    # ========================================================
    # Register agent
    # ========================================================

    def register_agent(
        self,
        agent_id: str,
        ip_address: str,
    ) -> None:

        with self._lock:

            self._agents[agent_id] = {

                "agent_id":
                agent_id,

                "ip_address":
                ip_address,

                "status":
                "online",

                "last_seen":
                self._current_time(),

            }

    # ========================================================
    # Update heartbeat
    # ========================================================

    def update_heartbeat(
        self,
        agent_id: str,
        ip_address: str | None = None,
    ) -> bool:

        with self._lock:

            if agent_id not in self._agents:

                return False

            self._agents[agent_id][
                "last_seen"
            ] = self._current_time()

            self._agents[agent_id][
                "status"
            ] = "online"

            if ip_address:

                self._agents[agent_id][
                    "ip_address"
                ] = ip_address

            return True

    # ========================================================
    # Get one agent
    # ========================================================

    def get_agent(
        self,
        agent_id: str,
    ) -> dict[str, str] | None:

        self.mark_stale_agents_offline()

        with self._lock:

            agent = self._agents.get(
                agent_id
            )

            if agent is None:

                return None

            return agent.copy()

    # ========================================================
    # Find agent by IP address
    # ========================================================

    def get_agent_by_ip(
        self,
        ip_address: str,
    ) -> dict[str, str] | None:

        self.mark_stale_agents_offline()

        with self._lock:

            for agent in self._agents.values():

                if (

                    agent.get(
                        "ip_address"
                    )

                    ==

                    ip_address

                ):

                    return agent.copy()

        return None

    # ========================================================
    # Mark stale agents offline
    # ========================================================

    def mark_stale_agents_offline(
        self,
    ) -> None:

        current_time = datetime.now(
            timezone.utc
        )

        with self._lock:

            for agent in self._agents.values():

                last_seen = datetime.fromisoformat(

                    agent["last_seen"]

                )

                if (

                    current_time
                    - last_seen

                    >

                    self._offline_threshold

                ):

                    agent["status"] = "offline"

    # ========================================================
    # Get all agents
    # ========================================================

    def get_agents(
        self,
    ) -> list[dict[str, str]]:

        self.mark_stale_agents_offline()

        with self._lock:

            return [

                agent.copy()

                for agent in self._agents.values()

            ]

    # ========================================================
    # Current UTC time
    # ========================================================

    @staticmethod
    def _current_time() -> str:

        return datetime.now(

            timezone.utc

        ).isoformat()