import asyncio
from .base import Platform, MessageHandler


class SlackPlatform(Platform):
    def __init__(self, token: str):
        self.token = token
        self._client = None
        self._app = None

    def _setup(self) -> None:
        try:
            from slack_sdk.web.async_client import AsyncWebClient
            from slack_bolt.async_app import AsyncApp
        except ImportError:
            raise ImportError("Install slack dependencies: pip install slack-sdk slack-bolt")

        self._app = AsyncApp(token=self.token)
        self._client = AsyncWebClient(token=self.token)

    async def start(self, handler: MessageHandler) -> None:
        self._setup()

        @self._app.event("message")
        async def on_message(event, say):
            if event.get("bot_id"):
                return
            user_id = event.get("user", "unknown")
            text = event.get("text", "")
            if not text:
                return
            response = await handler(user_id, text)
            await say(response)

        from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
        socket_handler = AsyncSocketModeHandler(self._app, self.token)
        await socket_handler.start_async()

    async def send(self, user_id: str, message: str) -> None:
        if self._client is None:
            self._setup()
        await self._client.chat_postMessage(channel=user_id, text=message)
