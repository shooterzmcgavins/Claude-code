from dataclasses import dataclass, field
from typing import Optional
import os

HAIKU = "claude-haiku-4-5"
SONNET = "claude-sonnet-4-6"
OPUS = "claude-opus-4-7"

MODEL_COSTS = {
    HAIKU: (1.0, 5.0),
    SONNET: (3.0, 15.0),
    OPUS: (5.0, 25.0),
}


@dataclass
class Config:
    # Provider: "anthropic" or "ollama"
    provider: str = field(default_factory=lambda: os.environ.get("PROVIDER", "anthropic"))

    # Anthropic
    api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))

    # Ollama
    ollama_base_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.environ.get("OLLAMA_MODEL", "llama3.2"))

    # Shared
    max_tokens: int = 4096
    max_context_turns: int = 20
    slack_token: Optional[str] = field(default_factory=lambda: os.environ.get("SLACK_BOT_TOKEN"))
    discord_token: Optional[str] = field(default_factory=lambda: os.environ.get("DISCORD_BOT_TOKEN"))
    telegram_token: Optional[str] = field(default_factory=lambda: os.environ.get("TELEGRAM_BOT_TOKEN"))

    def __post_init__(self):
        if self.provider == "anthropic" and not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when PROVIDER=anthropic")
        if self.provider not in ("anthropic", "ollama"):
            raise ValueError(f"Unknown PROVIDER '{self.provider}' — use 'anthropic' or 'ollama'")

    @property
    def is_ollama(self) -> bool:
        return self.provider == "ollama"
