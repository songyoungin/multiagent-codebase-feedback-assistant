"""Application settings management."""

from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    openai_model: str = "openai/gpt-4o-mini"
    bind_host: str = "0.0.0.0"  # Shared bind host for all agents
    project_scanner_agent_url: str = "http://localhost:8301"
    filesystem_mcp_enabled: bool = True

    def get_port_from_url(self, url: str) -> int:
        """Extract port number from URL.

        Args:
            url: URL to parse

        Returns:
            Port number (defaults: http=80, https=443)
        """
        parsed = urlparse(url)
        if parsed.port:
            return parsed.port
        return 443 if parsed.scheme == "https" else 80


settings = AppSettings()
