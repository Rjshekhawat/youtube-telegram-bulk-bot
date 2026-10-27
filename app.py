"""Single Telegram bot with independent channel modules."""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config
from modules.news import publish_news
from modules.questions import publish_question
from modules.documents import publish_pdf

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("bot-manager")


def is_admin(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id in config.ADMIN_USER_IDS)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "नमस्ते! Special Education Needs Bot Manager चालू है।\n\n"
        "/status — चैनल सेटिंग देखें\n"
        "/news संदेश — News चैनल पर पोस्ट करें\n"
        "/question प्रश्न — Question चैनल पर पोस्ट करें\n"
        "/pdf टेक्स्ट — PDF बनाकर Document चैनल पर भेजें\n"
        "/help — सहायता"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = [
        "Bot Manager status",
        f"News channel: {'configured' if config.NEWS_CHANNEL_ID else 'not configured'}",
        f"Question channel: {'configured' if config.QUESTION_CHANNEL_ID else 'not configured'}",
        f"Document channel: {'configured' if config.DOCUMENT_CHANNEL_ID else 'not configured'}",
        f"Admin IDs: {len(config.ADMIN_USER_IDS)} configured",
    ]
    await update.effective_message.reply_text("\n".join(lines))


async def admin_publish(update: Update, context: ContextTypes.DEFAULT_TYPE, kind: str) -> None:
    if not is_admin(update):
        await update.effective_message.reply_text("यह कमांड केवल अधिकृत एडमिन चला सकते हैं।")
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.effective_message.reply_text(
            "कमांड के बाद सामग्री लिखें। उदाहरण: /" + kind + " आज की महत्वपूर्ण खबर"
        )
        return

    try:
        if kind == "news":
            target = config.NEWS_CHANNEL_ID
            action = publish_news
        elif kind == "question":
            target = config.QUESTION_CHANNEL_ID
            action = publish_question
        else:
            target = config.DOCUMENT_CHANNEL_ID
            action = publish_pdf

        if not target:
            await update.effective_message.reply_text(
                f"{kind} चैनल सेट नहीं है। Hosting Environment में संबंधित CHANNEL_ID भरें।"
            )
            return
        await action(context.bot, target, text)
        await update.effective_message.reply_text("सफलतापूर्वक भेज दिया गया।")
    except Exception:
        logger.exception("Module '%s' failed", kind)
        await update.effective_message.reply_text(
            f"{kind} मॉड्यूल में त्रुटि आई। बाकी मॉड्यूल चलते रहेंगे। Logs में कारण देखें।"
        )


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_publish(update, context, "news")


async def question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_publish(update, context, "question")


async def pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_publish(update, context, "pdf")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled Telegram update error", exc_info=context.error)


def main() -> None:
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing.")
    if not config.ADMIN_USER_IDS:
        logger.warning("ADMIN_USER_IDS is empty; publishing commands will be blocked.")
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("question", question))
    app.add_handler(CommandHandler("pdf", pdf))
    app.add_error_handler(error_handler)
    logger.info("Bot Manager is starting.")
    app.run_polling(drop_pending_updates=False)


if __name__ == "__main__":
    main()
