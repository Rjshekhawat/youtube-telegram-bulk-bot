"""Single Telegram bot with independent, dynamically configured channel modules."""
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config
from modules.channel_store import add_channel, remove_channel, list_channels, get_channels
from modules.news import publish_news
from modules.questions import publish_question
from modules.documents import publish_pdf

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("bot-manager")

MODULE_NAMES = {"news": "News", "question": "Questions", "pdf": "PDF / Documents"}
MODULE_ACTIONS = {"news": publish_news, "question": publish_question, "pdf": publish_pdf}


def is_admin(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id in config.ADMIN_USER_IDS)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "नमस्ते! Special Education Needs Bot Manager चालू है।\n\n"
        "📌 चैनल मैनेजमेंट\n"
        "/addchannel news @channelusername — News चैनल जोड़ें\n"
        "/addchannel question @channelusername — Question चैनल जोड़ें\n"
        "/addchannel pdf @channelusername — PDF चैनल जोड़ें\n"
        "/channels — सभी चैनल देखें\n"
        "/removechannel ID — चैनल हटाएँ\n"
        "/status — सेटिंग देखें\n\n"
        "📤 पोस्टिंग\n"
        "/news संदेश — सभी News चैनलों पर पोस्ट\n"
        "/question प्रश्न — सभी Question चैनलों पर पोस्ट\n"
        "/pdf टेक्स्ट — सभी PDF चैनलों पर PDF भेजें\n\n"
        "चैनल में पोस्ट करने के लिए बॉट को उस चैनल का Administrator बनाना जरूरी है।"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.effective_message.reply_text("यह कमांड केवल अधिकृत एडमिन चला सकते हैं।")
        return
    rows = list_channels()
    counts = {key: len(get_channels(key)) for key in MODULE_NAMES}
    await update.effective_message.reply_text(
        "Bot Manager status\n"
        + "\n".join(f"{MODULE_NAMES[k]}: {counts[k]} चैनल" for k in MODULE_NAMES)
        + f"\nAdmin IDs: {len(config.ADMIN_USER_IDS)} configured"
        + f"\nकुल कॉन्फ़िगर चैनल: {len(rows)}"
    )


async def addchannel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.effective_message.reply_text("यह कमांड केवल अधिकृत एडमिन चला सकते हैं।")
        return
    if len(context.args) < 2:
        await update.effective_message.reply_text(
            "ऐसे लिखें:\n/addchannel news @channelusername\n"
            "/addchannel question @channelusername\n/addchannel pdf @channelusername"
        )
        return
    module, chat_id = context.args[0].lower(), context.args[1]
    if module not in MODULE_NAMES:
        await update.effective_message.reply_text("काम चुनें: news, question या pdf")
        return
    try:
        created = add_channel(module, chat_id)
        await update.effective_message.reply_text(
            ("चैनल जोड़ दिया गया।" if created else "यह चैनल पहले से जोड़ा हुआ है.")
            + "\nकाम: " + MODULE_NAMES[module]
            + "\nयाद रखें: बॉट को चैनल में Administrator बनाकर पोस्ट करने की अनुमति दें।"
        )
    except Exception:
        logger.exception("Could not add channel")
        await update.effective_message.reply_text("चैनल नहीं जुड़ पाया। जानकारी जाँचकर फिर प्रयास करें।")


async def channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.effective_message.reply_text("यह कमांड केवल अधिकृत एडमिन चला सकते हैं।")
        return
    rows = list_channels()
    if not rows:
        await update.effective_message.reply_text(
            "अभी कोई चैनल नहीं जुड़ा है। /addchannel news @channelusername से शुरू करें।"
        )
        return
    lines = ["जोड़े गए चैनल:"]
    lines.extend(f"ID {row[0]} | {MODULE_NAMES.get(row[1], row[1])} | {row[2]}" for row in rows)
    lines.append("\nहटाने के लिए: /removechannel ID")
    await update.effective_message.reply_text("\n".join(lines))


async def removechannel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.effective_message.reply_text("यह कमांड केवल अधिकृत एडमिन चला सकते हैं।")
        return
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("ऐसे लिखें: /removechannel 2 (ID /channels में दिखेगी)")
        return
    removed = remove_channel(int(context.args[0]))
    await update.effective_message.reply_text("चैनल हटा दिया गया।" if removed else "यह ID नहीं मिली।")


async def admin_publish(update: Update, context: ContextTypes.DEFAULT_TYPE, kind: str) -> None:
    if not is_admin(update):
        await update.effective_message.reply_text("यह कमांड केवल अधिकृत एडमिन चला सकते हैं।")
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.effective_message.reply_text("कमांड के बाद सामग्री लिखें। उदाहरण: /" + kind + " आज की महत्वपूर्ण खबर")
        return
    targets = get_channels(kind)
    if not targets:
        await update.effective_message.reply_text(
            f"अभी {MODULE_NAMES[kind]} चैनल नहीं जुड़ा है। पहले /addchannel {kind} @channelusername चलाएँ।"
        )
        return

    sent, failed = 0, []
    action = MODULE_ACTIONS[kind]
    for target in targets:
        try:
            await action(context.bot, target, text)
            sent += 1
        except Exception as exc:
            logger.exception("Module '%s' failed for destination %s", kind, target)
            failed.append(target)
    message = f"{sent}/{len(targets)} चैनल पर सफलतापूर्वक भेजा गया।"
    if failed:
        message += "\nइन चैनलों पर भेजने में समस्या हुई: " + ", ".join(failed)
        message += "\nबॉट की Admin permission और channel ID जाँचें।"
    await update.effective_message.reply_text(message)


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_publish(update, context, "news")


async def question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_publish(update, context, "question")


async def pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_publish(update, context, "pdf")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled Telegram update error", exc_info=context.error)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"Special Education Needs Bot Manager is running."
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        logger.info("Health check: " + format, *args)


def start_health_server() -> None:
    # Render Web Services require an HTTP listener on 0.0.0.0:$PORT.
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info("Health endpoint listening on port %s", port)


def main() -> None:
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing.")
    if not config.ADMIN_USER_IDS:
        logger.warning("ADMIN_USER_IDS is empty; management commands will be blocked.")
    start_health_server()\n    app = Application.builder().token(config.BOT_TOKEN).build()\n    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("addchannel", addchannel))
    app.add_handler(CommandHandler("channels", channels))
    app.add_handler(CommandHandler("removechannel", removechannel))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("question", question))
    app.add_handler(CommandHandler("pdf", pdf))
    app.add_error_handler(error_handler)
    logger.info("Bot Manager is starting.")
    app.run_polling(drop_pending_updates=False)


if __name__ == "__main__":
    main()
