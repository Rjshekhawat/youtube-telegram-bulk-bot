"""Environment-based configuration. Never store real secrets in this file."""
import os


def _optional(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


BOT_TOKEN = _optional(os.getenv("BOT_TOKEN"))
NEWS_CHANNEL_ID = _optional(os.getenv("NEWS_CHANNEL_ID"))
QUESTION_CHANNEL_ID = _optional(os.getenv("QUESTION_CHANNEL_ID"))
DOCUMENT_CHANNEL_ID = _optional(os.getenv("DOCUMENT_CHANNEL_ID"))
ADMIN_USER_IDS = {
    int(part.strip())
    for part in os.getenv("ADMIN_USER_IDS", "").split(",")
    if part.strip().isdigit()
}
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
