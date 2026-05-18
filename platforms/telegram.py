from .base import Platform, MessageHandler


class TelegramPlatform(Platform):
    def __init__(self, token: str):
        self.token = token

    async def start(self, handler: MessageHandler) -> None:
        try:
            from telegram import Update
            from telegram.ext import ApplicationBuilder, MessageHandler as TGHandler, filters
        except ImportError:
            raise ImportError("Install telegram dependency: pip install python-telegram-bot")

        async def on_message(update: Update, context) -> None:
            if not update.message or not update.message.text:
                return
            user_id = str(update.message.chat_id)
            response = await handler(user_id, update.message.text)
            await update.message.reply_text(response[:4096])  # Telegram 4096 char limit

        app = ApplicationBuilder().token(self.token).build()
        app.add_handler(TGHandler(filters.TEXT & ~filters.COMMAND, on_message))
        self._app = app

        print("Telegram: starting polling...")
        await app.run_polling()

    async def send(self, user_id: str, message: str) -> None:
        try:
            from telegram import Bot
        except ImportError:
            raise ImportError("Install telegram dependency: pip install python-telegram-bot")
        bot = Bot(token=self.token)
        await bot.send_message(chat_id=int(user_id), text=message[:4096])
