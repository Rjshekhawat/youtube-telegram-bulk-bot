"""News-channel publishing functions."""
from telegram import Bot


async def publish_news(bot: Bot, channel_id: str, text: str) -> None:
    if not text.strip():
        raise ValueError("News text is empty.")
    await bot.send_message(
        chat_id=channel_id,
        text=f"📰 शिक्षा एवं समाचार अपडेट\n\n{text.strip()}",
        disable_web_page_preview=False,
    )
