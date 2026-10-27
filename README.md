# Special Education Needs — Modular Telegram Bot Manager

A single Telegram bot with separate modules for different channel jobs. Designed for setup from a mobile phone without editing Python code for routine changes.

## Modules
- News: send a news item to the configured news channel.
- Questions: send MCQs to the configured question channel.
- Documents: turn supplied text into a PDF and send it to the configured document channel.
- Health: check bot status and configured destinations.

## Important
This is a starter framework, not yet a fully automatic news scraper or a complete quiz platform. News sources, schedules, and quiz-to-document workflows can be added module-by-module without changing unrelated modules. The previous YouTube download dependency is retained in requirements for future integration, but its original workflow has not yet been reconnected to this starter entry point.

## Setup
1. Create a Telegram bot with BotFather and copy its token privately.
2. Add the bot as an administrator to each destination channel, with permission to post messages/documents.
3. Deploy this repository on a suitable always-on Python host.
4. Add environment variables from `.env.example` in the host's Environment / Secrets settings.
5. Start with one test channel and test each module before enabling more.

Never put bot tokens in source files, GitHub commits, screenshots, or chat messages. If a token has been exposed, revoke it using BotFather and replace it.

## Configuration
- `BOT_TOKEN`: token for the one manager bot
- `NEWS_CHANNEL_ID`: target news channel ID (optional)
- `QUESTION_CHANNEL_ID`: target questions channel ID (optional)
- `DOCUMENT_CHANNEL_ID`: target PDF/document channel ID (optional)
- `ADMIN_USER_IDS`: comma-separated Telegram user IDs allowed to run admin commands

Channel IDs may be numeric IDs (often negative for channels) or public channel usernames such as `@your_channel`.

## Commands
- `/start` — welcome and command list
- `/status` — show channel counts
- `/addchannel news @channelusername` — add a News destination
- `/addchannel question @channelusername` — add a Questions destination
- `/addchannel pdf @channelusername` — add a PDF destination
- `/channels` — list destinations and their IDs
- `/removechannel ID` — remove one destination
- `/news Your news text` — publish to all configured News destinations
- `/question Your question and options` — publish to all configured Questions destinations
- `/pdf Your document text` — create and publish a PDF to all configured PDF destinations
- `/help` — show help

Publishing commands are restricted to configured admin user IDs.

## Adding channels from Telegram
1. Add the bot as an administrator to the target channel and allow it to post messages/documents.
2. Open a private chat with the bot and run `/addchannel news @yourchannel`, or use `question` / `pdf` instead of `news`.
3. Use `/channels` to check the list. Use `/removechannel ID` to remove a destination.
4. Set `ADMIN_USER_IDS` in hosting secrets to your numeric Telegram user ID; only those IDs can change channels or publish. Never leave this blank in production.

Channel settings are stored in SQLite (`bot_manager.sqlite3`). The host must provide persistent disk/storage for these settings to survive redeploys or restarts. Do not rely on an ephemeral filesystem.

## Stability design
Each module is kept in its own file. A module-level error is logged and returned as a clear message; it should not terminate the bot process. Keep backups before making changes and test changes before deployment. No architecture can guarantee zero downtime, and free hosting may sleep or stop services.

## Project layout
```
app.py
config.py
modules/
  news.py
  questions.py
  documents.py
requirements.txt
.env.example
```
