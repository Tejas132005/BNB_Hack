"""
NeutraYield AI — Telegram Inline Keyboard Builder
All keyboard layouts for the bot UI.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard():
    """
    Main action keyboard shown after /start and market scan.
    Layout:
        [ Buy ] [ Sell ]
        [ Stop ] [ Limit ]
        [ 🧠 AI Analysis ]
        [ ❌ End Session ]
    """
    keyboard = [
        [
            InlineKeyboardButton("💰 Buy", callback_data="action_buy"),
            InlineKeyboardButton("📉 Sell", callback_data="action_sell"),
        ],
        [
            InlineKeyboardButton("🛑 Stop", callback_data="action_stop"),
            InlineKeyboardButton("📊 Limit", callback_data="action_limit"),
        ],
        [
            InlineKeyboardButton("🧠 AI Analysis", callback_data="ai_analysis"),
        ],
        [
            InlineKeyboardButton("🔄 Refresh Scan", callback_data="refresh_scan"),
        ],
        [
            InlineKeyboardButton("❌ End Session", callback_data="end_session"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_menu_keyboard():
    """
    Simple back-to-menu keyboard for sub-pages.
    """
    keyboard = [
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu"),
        ],
        [
            InlineKeyboardButton("❌ End Session", callback_data="end_session"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_trade_result_keyboard(tx_id=None, web_url=None):
    """
    Keyboard shown after a trade action is prepared.
    Includes a link to execute in the web interface (non-custodial).
    """
    buttons = []

    if web_url:
        buttons.append([
            InlineKeyboardButton("🌐 Execute in Web Interface", url=web_url),
        ])

    buttons.extend([
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu"),
        ],
        [
            InlineKeyboardButton("❌ End Session", callback_data="end_session"),
        ],
    ])

    return InlineKeyboardMarkup(buttons)


def get_start_keyboard():
    """
    Initial keyboard for brand new users before first scan.
    """
    keyboard = [
        [
            InlineKeyboardButton("🚀 Start Market Scan", callback_data="refresh_scan"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
