"""
NeutraYield AI — Telegram Bot Entry Point
Runs in polling mode for hackathon demo.
Uses python-telegram-bot v20+ async architecture.

Usage:
    python telegram_bot/bot.py
"""

import os
import sys
import logging
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────
#  Environment & Django Bootstrap
# ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Add project root to path so we can import core modules
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bnb_hack.settings")

import django
django.setup()

# ─────────────────────────────────────────────────────────────
#  Telegram Bot Imports (after Django bootstrap)
# ─────────────────────────────────────────────────────────────
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)

from telegram_bot.handlers import (
    start_command,
    end_command,
    button_callback,
    error_handler,
)

# ─────────────────────────────────────────────────────────────
#  Logging
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Reduce noise from httpx
logging.getLogger("httpx").setLevel(logging.WARNING)


# ─────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────
def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        logger.error(
            "TELEGRAM_BOT_TOKEN not found in environment variables.\n"
            "Please set it in your .env file:\n"
            "  TELEGRAM_BOT_TOKEN=your-bot-token-here"
        )
        sys.exit(1)

    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("  🚀  NeutraYield AI Telegram Bot Starting")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"  Django settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    logger.info(f"  Mode: Polling (Hackathon Demo)")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Build the application with increased timeouts for local stability
    app = (
        ApplicationBuilder()
        .token(token)
        .read_timeout(30)
        .connect_timeout(30)
        .build()
    )

    # ── Register Command Handlers ──
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("end", end_command))

    # ── Register Callback Query Handler (inline buttons) ──
    app.add_handler(CallbackQueryHandler(button_callback))

    # ── Register Error Handler ──
    app.add_error_handler(error_handler)

    # ── Start Polling ──
    logger.info("✅  Bot is now polling for updates...")
    app.run_polling(
        drop_pending_updates=True,  # Ignore old messages on restart
        allowed_updates=["message", "callback_query"],
    )


if __name__ == "__main__":
    main()
