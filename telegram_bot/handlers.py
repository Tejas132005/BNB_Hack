"""
NeutraYield AI — Telegram Bot Callback & Command Handlers
Uses python-telegram-bot v20+ async handlers.
All business logic delegated to services_bridge.py → Django services.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .services_bridge import TelegramServiceBridge
from .keyboards import (
    get_main_menu_keyboard,
    get_back_to_menu_keyboard,
    get_trade_result_keyboard,
    get_start_keyboard,
)

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════
#  UTILITY: Format helpers
# ═════════════════════════════════════════════════════════════

def _signal_emoji(signal: str) -> str:
    """Returns emoji for the signal type."""
    return {
        "BUY": "🟢",
        "SELL": "🔴",
        "STOP": "🛑",
        "LIMIT": "📊",
    }.get(signal.upper(), "⚪")


def _risk_emoji(risk: str) -> str:
    """Returns emoji for risk level."""
    risk_lower = risk.lower()
    if "low" in risk_lower:
        return "🟢"
    elif "medium" in risk_lower or "moderate" in risk_lower:
        return "🟡"
    elif "high" in risk_lower:
        return "🔴"
    return "⚪"


def _format_scan_message(scan: dict) -> str:
    """
    Builds a beautifully formatted scan result message.
    """
    signal = scan["signal"]
    confidence = scan["confidence"]
    risk = scan["riskLevel"]
    factors = scan.get("factors", [])
    explanation = scan.get("explanation", "")

    # Truncate explanation for Telegram readability
    if len(explanation) > 400:
        explanation = explanation[:397] + "..."

    # Build factors list
    factors_text = ""
    if factors:
        factors_text = "\n".join(f"  • {f}" for f in factors[:5])

    msg = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊  *Market Scan Complete\\!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{_signal_emoji(signal)}  *Signal:*  `{signal}`\n"
        f"📈  *Confidence:*  `{confidence}%`\n"
        f"{_risk_emoji(risk)}  *Risk Level:*  `{risk}`\n"
    )

    if factors_text:
        msg += (
            f"\n🧠  *AI Key Insights:*\n"
            f"{factors_text}\n"
        )

    if explanation:
        # Escape MarkdownV2 special chars in explanation
        safe_explanation = _escape_md(explanation)
        msg += (
            f"\n💡  *Analysis:*\n"
            f"_{safe_explanation}_\n"
        )

    msg += (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⛓  *Network:*  BNB Chain Testnet\n"
        f"🤖  *Powered by:*  NeutraYield AI\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n_Select an action below:_"
    )

    return msg


def _escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


# ═════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ═════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start — Welcome message + trigger initial market scan.
    """
    user = update.effective_user
    welcome_msg = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀  *Welcome to NeutraYield AI*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Hello *{_escape_md(user.first_name)}*\\! 👋\n\n"
        f"I'm your AI\\-powered DeFi assistant\n"
        f"running on *BNB Chain Testnet*\\.\n\n"
        f"🔹 Real\\-time market scanning\n"
        f"🔹 AI\\-driven trading signals\n"
        f"🔹 Non\\-custodial execution\n"
        f"🔹 Portfolio risk analysis\n\n"
        f"_Tap the button below to start\\!_"
    )

    await update.message.reply_text(
        welcome_msg,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=get_start_keyboard(),
    )

    # Auto-trigger scan for speed
    await _do_market_scan(update, context, is_initial=True)


async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /end — Close session cleanly.
    """
    msg = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋  *Session Closed*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Your session has been ended\\.\n"
        f"No data stored\\. No keys retained\\.\n\n"
        f"_Restart anytime with /start_"
    )

    await update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


# ═════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLERS
# ═════════════════════════════════════════════════════════════

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Routes all inline keyboard button presses.
    """
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    data = query.data

    if data == "refresh_scan":
        await _do_market_scan(update, context)

    elif data == "ai_analysis":
        await _do_ai_analysis(update, context)

    elif data in ("action_buy", "action_sell", "action_stop", "action_limit"):
        action_map = {
            "action_buy": "BUY",
            "action_sell": "SELL",
            "action_stop": "STOP",
            "action_limit": "LIMIT",
        }
        await _do_execute_trade(update, context, action_map[data])

    elif data == "back_to_menu":
        await _do_market_scan(update, context)

    elif data == "end_session":
        await _do_end_session(update, context)


# ═════════════════════════════════════════════════════════════
#  INTERNAL ACTION FUNCTIONS
# ═════════════════════════════════════════════════════════════

async def _do_market_scan(update: Update, context: ContextTypes.DEFAULT_TYPE, is_initial=False):
    """
    Executes market scan and sends formatted result.
    Shows "Scanning…" indicator for UX.
    """
    # Determine where to send/edit
    if update.callback_query:
        msg = update.callback_query.message
        # Show loading state
        await msg.edit_text(
            "🔄  *Scanning markets\\.\\.\\.*\n\n"
            "_Analyzing RSI, MACD, volatility & funding rates\\.\\.\\._",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        msg = await update.message.reply_text(
            "🔄  *Scanning markets\\.\\.\\.*\n\n"
            "_Analyzing RSI, MACD, volatility & funding rates\\.\\.\\._",
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    # Call backend
    scan = await TelegramServiceBridge.scan_market()

    if not scan.get("success"):
        error_msg = (
            "⚠️  *Market scan temporarily unavailable\\.*\n\n"
            "_Please try again shortly\\._"
        )
        if update.callback_query:
            await msg.edit_text(
                error_msg,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=get_back_to_menu_keyboard(),
            )
        else:
            await msg.edit_text(
                error_msg,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=get_back_to_menu_keyboard(),
            )
        return

    # Format and send scan result
    scan_text = _format_scan_message(scan)

    try:
        await msg.edit_text(
            scan_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=get_main_menu_keyboard(),
        )
    except Exception as e:
        # Fallback: send without MarkdownV2 if parsing fails
        logger.warning(f"MarkdownV2 parse failed, falling back: {e}")
        fallback = _format_scan_fallback(scan)
        await msg.edit_text(
            fallback,
            reply_markup=get_main_menu_keyboard(),
        )


def _format_scan_fallback(scan: dict) -> str:
    """Plain text fallback if MarkdownV2 fails."""
    signal = scan["signal"]
    confidence = scan["confidence"]
    risk = scan["riskLevel"]
    factors = scan.get("factors", [])
    explanation = scan.get("explanation", "")

    factors_str = "\n".join(f"  • {f}" for f in factors[:5]) if factors else "N/A"
    if len(explanation) > 300:
        explanation = explanation[:297] + "..."

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊  Market Scan Complete!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{_signal_emoji(signal)}  Signal:  {signal}\n"
        f"📈  Confidence:  {confidence}%\n"
        f"{_risk_emoji(risk)}  Risk Level:  {risk}\n\n"
        f"🧠  AI Key Insights:\n{factors_str}\n\n"
        f"💡  Analysis:\n{explanation}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⛓  Network:  BNB Chain Testnet\n"
        f"🤖  Powered by:  NeutraYield AI\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Select an action below:"
    )


async def _do_ai_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Deep AI analysis via Groq LLM.
    Shows loading indicator, then edits with result.
    """
    msg = update.callback_query.message

    # Loading indicator
    await msg.edit_text(
        "🤖  *Generating AI insights\\.\\.\\.*\n\n"
        "_NeutraYield AI is analyzing market conditions\\.\\.\\._\n"
        "_This may take a few seconds\\._",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    # Call backend
    result = await TelegramServiceBridge.get_ai_analysis()

    if not result.get("success"):
        await msg.edit_text(
            "⚠️  *AI analysis temporarily unavailable\\.*\n\n"
            "_Please try again shortly\\._",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=get_back_to_menu_keyboard(),
        )
        return

    analysis = result["analysis"]
    if len(analysis) > 3500:
        analysis = analysis[:3497] + "..."

    safe_analysis = _escape_md(analysis)

    analysis_msg = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧠  *NeutraYield AI Analysis*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{safe_analysis}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖  _Powered by Groq Llama\\-3_\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    try:
        await msg.edit_text(
            analysis_msg,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=get_back_to_menu_keyboard(),
        )
    except Exception as e:
        logger.warning(f"MarkdownV2 parse failed for analysis: {e}")
        await msg.edit_text(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠  NeutraYield AI Analysis\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{analysis}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖  Powered by Groq Llama-3\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=get_back_to_menu_keyboard(),
        )


async def _do_execute_trade(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    """
    Executes a real transaction on-chain and sends confirmation + Tx details.
    """
    msg = update.callback_query.message

    action_emojis = {"BUY": "💰", "SELL": "📉", "STOP": "🛑", "LIMIT": "📊"}
    emoji = action_emojis.get(action, "⚡")

    await msg.edit_text(
        f"{emoji}  *Executing {action} on BNB Testnet\\.\\.\\.*\n\n"
        f"_Signing and broadcasting transaction\\.\\.\\._",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    # Call backend
    result = await TelegramServiceBridge.execute_trade(action)

    if not result.get("success"):
        error = result.get("error", "Unknown error")
        await msg.edit_text(
            f"⚠️  *Execution Failed\\.*\n\n"
            f"Error: _{_escape_md(error)}_\n\n"
            f"_Please check if your wallet has enough tBNB\\._",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=get_back_to_menu_keyboard(),
        )
        return

    explorer_url = result.get("explorer_url", "")
    tx_hash = result.get("tx_hash", "N/A")

    trade_msg = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅  *{_escape_md(action)} Trade Confirmed\\!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💲  *Price:*  `${result['price']}`\n"
        f"📊  *Confidence:*  `{result['confidence']}%`\n"
        f"⛽  *Gas Fee:*  `{result.get('gas_fee_bnb', '~0.0003')} BNB`\n"
        f"💎  *Amount:*  `0.0001 BNB`\n"
        f"⛓  *Network:*  `BNB Chain Testnet`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗  *Transaction Details*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔  *Hash:*  `{_escape_md(tx_hash[:16])}...` \n"
        f"🕒  *Status:*  `Mined & Confirmed` \n\n"
        f"👉  _Click below to view on BscScan_"
    )

    try:
        await msg.edit_text(
            trade_msg,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=get_trade_result_keyboard(web_url=explorer_url),
        )
    except Exception as e:
        logger.warning(f"MarkdownV2 parse failed for trade: {e}")
        fallback = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ {action} Trade Confirmed!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💲 Price: ${result['price']}\n"
            f"📊 Confidence: {result['confidence']}%\n"
            f"⛽ Gas Fee: {result.get('gas_fee_bnb', 'N/A')} BNB\n\n"
            f"🔗 Transaction Hash:\n{tx_hash}"
        )
        await msg.edit_text(
            fallback,
            reply_markup=get_trade_result_keyboard(web_url=explorer_url),
        )


async def _do_end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ends the session, removes inline keyboard.
    """
    msg = update.callback_query.message

    end_msg = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋  *Session Closed*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Your session has been ended\\.\n"
        f"🔐  No data stored\\. No keys retained\\.\n\n"
        f"_Restart anytime with /start_"
    )

    try:
        await msg.edit_text(
            end_msg,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    except Exception:
        await msg.edit_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👋  Session Closed\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Your session has been ended.\n"
            "🔐  No data stored. No keys retained.\n\n"
            "Restart anytime with /start"
        )


# ═════════════════════════════════════════════════════════════
#  ERROR HANDLER
# ═════════════════════════════════════════════════════════════

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Global error handler for the bot.
    """
    logger.error(f"Telegram bot error: {context.error}", exc_info=context.error)

    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An unexpected error occurred.\n"
                "Please try again or use /start to restart."
            )
        except Exception:
            pass
