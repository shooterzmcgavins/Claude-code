from abc import ABC, abstractmethod
from typing import Callable, Awaitable

MessageHandler = Callable[[str, str], Awaitable[str]]  # (user_id, message) -> response


class Platform(ABC):
    @abstractmethod
    async def start(self, handler: MessageHandler) -> None:
        """Start listening for messages and call handler for each one."""

    @abstractmethod
    async def send(self, user_id: str, message: str) -> None:
        """Send a message to a user."""
