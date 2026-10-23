"""Application configuration loaded from environment variables / ``.env``."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from a2a_agent import __version__


class Settings(BaseSettings):
    """Runtime settings.

    Every field can be overridden with an environment variable prefixed with
    ``A2A_`` (e.g. ``A2A_PORT=8000``) or through a ``.env`` file.
    """

    model_config = SettingsConfigDict(
        env_prefix="A2A_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Agent identity ---------------------------------------------------
    agent_name: str = "LangChain A2A Agent"
    agent_description: str = (
        "General purpose assistant exposed through the Agent2Agent (A2A) "
        "protocol. Powered by LangChain, LangGraph and FastAPI."
    )
    agent_version: str = __version__

    # --- HTTP server ------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 9999
    public_url: str | None = Field(
        default=None,
        description=(
            "Public base URL advertised in the Agent Card. Defaults to "
            "http://{host}:{port} (0.0.0.0 is replaced by 127.0.0.1)."
        ),
    )
    cors_origins: list[str] = Field(default_factory=list)
    log_level: str = "INFO"

    # --- LLM --------------------------------------------------------------
    model: str = Field(
        default="openai:gpt-4o-mini",
        description=(
            "LangChain model identifier, e.g. 'openai:gpt-4o-mini'. "
            "For OpenAI-compatible servers (Ollama, vLLM, LM Studio) set "
            "OPENAI_BASE_URL and use an 'openai:<model>' identifier."
        ),
    )
    temperature: float = 0.0
    max_tokens: int | None = None

    # --- A2A --------------------------------------------------------------
    streaming: bool = Field(
        default=True,
        description="Advertise and use token streaming in the Agent Card.",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def base_url(self) -> str:
        """Base URL advertised to A2A clients (no trailing slash)."""
        if self.public_url:
            return self.public_url.rstrip("/")
        host = "127.0.0.1" if self.host in {"0.0.0.0", "::"} else self.host
        return f"http://{host}:{self.port}"


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
