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
    api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    default_model: str = HAIKU
    max_model: str = SONNET
    max_tokens: int = 4096
    max_context_turns: int = 20
    slack_token: Optional[str] = field(default_factory=lambda: os.environ.get("SLACK_BOT_TOKEN"))
    discord_token: Optional[str] = field(default_factory=lambda: os.environ.get("DISCORD_BOT_TOKEN"))
    telegram_token: Optional[str] = field(default_factory=lambda: os.environ.get("TELEGRAM_BOT_TOKEN"))

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
