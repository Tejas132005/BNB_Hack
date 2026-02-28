"""
NeutraYield AI — Django Service Bridge for Telegram Bot
Calls existing Django services directly (no HTTP, no logic duplication).
All business logic remains centralized in core/engines and core/services.
"""

import os
import sys
import json
import logging
import uuid

# ─────────────────────────────────────────────────────────────
#  Bootstrap Django so we can import core models + services
# ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bnb_hack.settings")

import django
django.setup()

# ─────────────────────────────────────────────────────────────
#  Now safe to import Django models and engines
# ─────────────────────────────────────────────────────────────
from asgiref.sync import sync_to_async
from core.engines.market_scanner import get_market_engine, MarketAnalyzer, BNBTradeExecutor
from core.engines.ai_agent import NeutraYieldAIAgent
from core.services.arbitrage import ArbitrageService
from core.services.delta_neutral import DeltaNeutralService
from core.services.yield_rotation import YieldRotationService
from core.services.risk_management import RiskManagementService
from core.models import AIActivityLog, UserPortfolio, TradeExecution

logger = logging.getLogger(__name__)

# Web interface base URL (for non-custodial trade execution links)
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://127.0.0.1:8000")


class TelegramServiceBridge:
    """
    Bridge layer between Telegram handlers and Django backend.
    All methods are static — wrapped in sync_to_async for async context.
    """

    # ─────────────────────────────────────────────────────────
    #  1. MARKET SCAN  (calls MarketDataEngine + MarketAnalyzer + LLM)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    @sync_to_async
    def scan_market():
        """
        Runs a full market scan using existing engines.
        Returns structured dict with signal, confidence, risk, factors,
        AI explanation, and risk summary.
        """
        try:
            engine = get_market_engine()
            dataset = engine.get_cached_or_generate(max_age=10)

            # Rule-based signal
            signal_result = MarketAnalyzer.analyze(dataset)

            # LLM explanation
            explanation = ""
            risk_summary = ""
            try:
                agent = NeutraYieldAIAgent()
                summary_text = BNBTradeExecutor.get_summary_for_llm(dataset)

                system_prompt = (
                    "You are a professional quantitative trading AI. "
                    "Analyze short-term market conditions using RSI, MACD, "
                    "volatility, funding rates and price momentum. "
                    "Respond in JSON with two keys: 'explanation' and 'riskSummary'. "
                    "Keep each under 100 words. Be concise and insightful."
                )

                user_prompt = (
                    f"{summary_text}\n\n"
                    f"Signal: {signal_result['signal']} "
                    f"(Confidence: {signal_result['confidence']}%, "
                    f"Risk: {signal_result['riskLevel']})\n"
                    f"Factors: {', '.join(signal_result.get('factors', []))}\n\n"
                    f"Explain this trading decision and provide a risk summary."
                )

                completion = agent.client.chat.completions.create(
                    model=agent.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=400,
                )

                llm_response = completion.choices[0].message.content
                try:
                    cleaned = llm_response.strip()
                    if cleaned.startswith("```"):
                        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
                        cleaned = cleaned.rsplit("```", 1)[0]
                    parsed = json.loads(cleaned)
                    explanation = parsed.get("explanation", llm_response)
                    risk_summary = parsed.get("riskSummary", "")
                except (json.JSONDecodeError, AttributeError):
                    explanation = llm_response
                    risk_summary = f"Risk Level: {signal_result['riskLevel']}"

            except Exception as e:
                logger.error(f"LLM scan error: {e}")
                explanation = "AI analysis temporarily unavailable."
                risk_summary = f"Risk Level: {signal_result['riskLevel']}"

            # Log the scan
            AIActivityLog.objects.create(
                event_type="Telegram Market Scan",
                message=f"Scanner: {signal_result['signal']} @ {signal_result['confidence']}% confidence",
                reasoning=explanation[:500],
                confidence_score=signal_result["confidence"] / 100,
            )

            return {
                "success": True,
                "signal": signal_result["signal"],
                "confidence": signal_result["confidence"],
                "riskLevel": signal_result["riskLevel"],
                "factors": signal_result.get("factors", []),
                "explanation": explanation,
                "riskSummary": risk_summary,
            }

        except Exception as e:
            logger.exception(f"Market scan failed: {e}")
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────
    #  2. AI ANALYSIS  (deep LLM reasoning via NeutraYieldAIAgent)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    @sync_to_async
    def get_ai_analysis():
        """
        Calls the Groq LLM for detailed market analysis.
        Mirrors the llm_analysis endpoint logic.
        """
        try:
            agent = NeutraYieldAIAgent()
            engine = get_market_engine()
            dataset = engine.get_cached_or_generate(max_age=10)
            summary_text = BNBTradeExecutor.get_summary_for_llm(dataset)

            # Also pull latest signal for context
            signal_result = MarketAnalyzer.analyze(dataset)

            system_prompt = (
                "You are NeutraYield AI, a professional quantitative trading AI "
                "running on BNB Chain. Provide a detailed market analysis covering:\n"
                "1. Current market conditions (price action, momentum)\n"
                "2. Technical indicators (RSI, MACD, Volume)\n"
                "3. Risk assessment and key concerns\n"
                "4. Recommended strategy (with confidence level)\n"
                "5. Key levels to watch\n\n"
                "Be concise but thorough. Use bullet points. "
                "Keep total response under 250 words."
            )

            signal_context = (
                f"Current Signal: {signal_result['signal']} | "
                f"Confidence: {signal_result['confidence']}% | "
                f"Risk: {signal_result['riskLevel']}"
            )

            user_prompt = (
                f"Provide a comprehensive market analysis.\n\n"
                f"Market Data:\n{summary_text}\n\n"
                f"Signal Context: {signal_context}\n"
                f"Analysis Factors: {', '.join(signal_result.get('factors', []))}"
            )

            completion = agent.client.chat.completions.create(
                model=agent.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=600,
            )

            response_text = completion.choices[0].message.content

            # Log the AI activity
            AIActivityLog.objects.create(
                event_type="Telegram AI Analysis",
                message="Deep AI analysis requested via Telegram bot.",
                reasoning=response_text[:500],
                confidence_score=signal_result["confidence"] / 100,
            )

            return {"success": True, "analysis": response_text}

        except Exception as e:
            logger.exception(f"AI analysis failed: {e}")
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────
    #  3. EXECUTE TRADE  (Real On-Chain Execution)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    @sync_to_async
    def execute_trade(action_type: str, wallet_address: str = "0xDemoAdminWallet"):
        """
        Executes a real transaction on BNB Testnet using the server-side wallet.
        This provides instant 'Trade Confirmed' feedback for the demo.
        """
        try:
            from core.engines.bnb_chain import execute_real_trade
            
            if action_type not in ("BUY", "SELL", "STOP", "LIMIT"):
                return {"success": False, "error": "Invalid action type."}

            engine = get_market_engine()
            dataset = engine.get_cached_or_generate(max_age=10)
            latest_price = dataset[-1]["price"] if dataset else 580.0

            # Execute real on-chain trade
            # Small 0.0001 BNB value for demo trades
            result = execute_real_trade(action_type, value_bnb=0.0001)

            if not result.get("success"):
                return result

            # Log the successful execution in Django models
            tx_hash = result.get("tx_hash")
            
            TradeExecution.objects.create(
                signal=action_type,
                executed_action=action_type,
                price=latest_price,
                executed_price=latest_price,
                amount=0.0001,
                tx_hash=tx_hash,
                chain="BNB Chain",
                wallet_address=result.get("wallet_address", wallet_address),
                status="Confirmed",
                confidence=0.9, # High confidence for direct execution
            )

            AIActivityLog.objects.create(
                event_type=f"Telegram Trade Executed ({action_type})",
                message=f"Real {action_type} trade confirmed on BNB Testnet.",
                reasoning=f"Tx Hash: {tx_hash} | Price: ${latest_price:.2f}",
                confidence_score=0.9,
            )

            # Add extra details for the bot message
            result["price"] = round(latest_price, 2)
            result["confidence"] = 90
            result["riskLevel"] = "Moderate"
            
            return result

        except Exception as e:
            logger.exception(f"Trade execution failed: {e}")
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────
    #  4. PORTFOLIO / RISK METRICS
    # ─────────────────────────────────────────────────────────
    @staticmethod
    @sync_to_async
    def get_portfolio_summary(wallet_address: str = "0xDemoUserAddress"):
        """
        Fetches portfolio metrics using existing RiskManagementService.
        """
        try:
            metrics = RiskManagementService.get_dashboard_metrics(wallet_address)
            return {"success": True, "metrics": metrics}
        except Exception as e:
            logger.exception(f"Portfolio fetch failed: {e}")
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────
    #  5. ARBITRAGE MONITORING
    # ─────────────────────────────────────────────────────────
    @staticmethod
    @sync_to_async
    def get_arbitrage_data():
        """
        Fetches latest arbitrage spread data.
        """
        try:
            monitoring = ArbitrageService.get_monitoring_data()
            spread = ArbitrageService.find_spread_opportunity()
            return {
                "success": True,
                "exchanges": monitoring,
                "opportunity": spread,
            }
        except Exception as e:
            logger.exception(f"Arbitrage data failed: {e}")
            return {"success": False, "error": str(e)}
