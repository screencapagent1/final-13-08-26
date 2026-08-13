import secrets


class AuthenticationManager:
    """
    Handles authentication of agents.
    """

    def __init__(
        self,
        api_key: str,
    ) -> None:
        self.api_key = api_key

    def verify_api_key(
        self,
        provided_key: str | None,
    ) -> bool:
        """
        Verify the provided API key.
        """

        if provided_key is None:
            return False

        return secrets.compare_digest(
            provided_key,
            self.api_key,
        )