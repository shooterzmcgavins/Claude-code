from .base import Platform, MessageHandler


class DiscordPlatform(Platform):
    def __init__(self, token: str):
        self.token = token
        self._client = None

    def _setup(self) -> None:
        try:
            import discord
        except ImportError:
            raise ImportError("Install discord dependency: pip install discord.py")

        intents = discord.Intents.default()
        intents.message_content = True
        self._discord = discord
        self._client = discord.Client(intents=intents)

    async def start(self, handler: MessageHandler) -> None:
        self._setup()
        client = self._client

        @client.event
        async def on_ready():
            print(f"Discord: logged in as {client.user}")

        @client.event
        async def on_message(message):
            if message.author == client.user:
                return
            user_id = str(message.author.id)
            response = await handler(user_id, message.content)
            await message.channel.send(response[:2000])  # Discord 2000 char limit

        await client.start(self.token)

    async def send(self, user_id: str, message: str) -> None:
        if self._client is None:
            self._setup()
        user = await self._client.fetch_user(int(user_id))
        await user.send(message[:2000])
