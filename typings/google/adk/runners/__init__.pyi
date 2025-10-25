"""Type stubs for google.adk.runners"""

from typing import Any, Optional

class Runner:
    """Runner for executing agents."""

    def __init__(
        self,
        *,
        app: Optional[Any] = None,
        app_name: Optional[str] = None,
        agent: Optional[Any] = None,
        plugins: Optional[list[Any]] = None,
        artifact_service: Optional[Any] = None,
        session_service: Any,
        memory_service: Optional[Any] = None,
        credential_service: Optional[Any] = None,
    ) -> None: ...

    async def close(self) -> None:
        """Close the runner and cleanup resources."""
        ...

    def run_async(self, **kwargs: Any) -> Any: ...
