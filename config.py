from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
import os
import warnings

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
    # Provider: "ollama" (default) or "anthropic"
    provider: str = field(default_factory=lambda: os.environ.get("PROVIDER", "ollama"))

    # Anthropic
    api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))

    # Ollama
    ollama_base_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b"))

    # Shared
    max_tokens: int = 4096
    max_context_turns: int = 20
    slack_token: Optional[str] = field(default_factory=lambda: os.environ.get("SLACK_BOT_TOKEN"))
    discord_token: Optional[str] = field(default_factory=lambda: os.environ.get("DISCORD_BOT_TOKEN"))
    telegram_token: Optional[str] = field(default_factory=lambda: os.environ.get("TELEGRAM_BOT_TOKEN"))

    def __post_init__(self):
        if self.provider == "anthropic" and not self.api_key:
            warnings.warn(
                "ANTHROPIC_API_KEY is not set; Anthropic provider will not work.",
                stacklevel=2,
            )
        if self.provider not in ("anthropic", "ollama"):
            warnings.warn(
                f"Unknown PROVIDER '{self.provider}' — use 'anthropic' or 'ollama'",
                stacklevel=2,
            )

    def validate(self) -> List[str]:
        """Return a list of configuration issues (does not raise)."""
        issues: List[str] = []
        if self.provider not in ("anthropic", "ollama"):
            issues.append(f"Unknown provider '{self.provider}' — use 'anthropic' or 'ollama'")
        if self.provider == "anthropic" and not self.api_key:
            issues.append("ANTHROPIC_API_KEY is not set")
        return issues

    @property
    def is_ollama(self) -> bool:
        return self.provider == "ollama"

    @property
    def active_model(self) -> str:
        if self.is_ollama:
            return self.ollama_model
        return SONNET  # default anthropic model

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "anthropic_api_key_set": bool(self.api_key),
            "max_tokens": self.max_tokens,
        }
