"""Question-channel publishing functions."""
from telegram import Bot


async def publish_question(bot: Bot, channel_id: str, text: str) -> None:
    if not text.strip():
        raise ValueError("Question text is empty.")
    await bot.send_message(
        chat_id=channel_id,
        text=f"📝 प्रश्न अभ्यास\n\n{text.strip()}",
        disable_web_page_preview=True,
    )
