import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class NeutraYieldAIAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def analyze_strategy(self, market_data, strategy_type="MODERATE"):
        """
        Analyzes market conditions and explains the strategy decision.
        """
        system_prompt = (
            "You are NeutraYield AI, a professional quantitative trading AI agent managing delta-neutral "
            "and arbitrage strategies on the BNB Chain. Your goal is to explain trading decisions clearly, "
            "conservatively, and transparently. Avoid hype. Focus on risk management and market-neutral yield."
        )
        
        user_prompt = f"""
        Market Conditions: {market_data}
        Current Strategy Mode: {strategy_type}
        
        Provide:
        1. A brief executive summary of the current market state.
        2. Reasoning for the selected strategy.
        3. A risk assessment (Net Exposure, Volatility, Liquidation Risk).
        4. A transparency log entry (e.g., 'Maintaining hedge at 0.98 delta').
        """
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error communicating with AI Agent: {str(e)}"

    def chat(self, user_query, portfolio_context=None):
        """
        Handles user queries about their portfolio or general strategy.
        """
        system_prompt = (
            "You are NeutraYield AI, the personal investment assistant for a user on the NeutraYield platform. "
            "You ONLY answer questions related to market analysis, DeFi strategies, BNB Chain, and portfolio management. "
            "If the user asks an unrelated question (e.g., about celebrities, general history, politics, or non-financial topics), "
            "you MUST reply exactly with: 'conversation is out of topic. I am assistant for market analyasis queries. Pls ask related questions.' "
            "Provide institutional-grade, data-driven answers for valid queries. Be transparent about risks."
        )
        
        context = f"\nUser Portfolio: {portfolio_context}" if portfolio_context else ""
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{user_query}{context}"}
                ],
                temperature=0.5,
                max_tokens=512,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"AI Agent is currently unavailable: {str(e)}"
