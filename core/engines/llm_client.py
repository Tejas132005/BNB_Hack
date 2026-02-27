import os
from groq import Groq

class LLMAnalyzer:
    """
    Uses Groq LLM to provide deep reasoning for arbitrage signals.
    """
    def __init__(self):
        self.api_key = os.environ.get('GROQ_API_KEY')
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None

    def refine_strategy(self, action, event_name, opp_details, confidence):
        if not self.client:
            return "LLM Analysis skipped (No API Key)."

        try:
            prompt = f"""
            Analyze the following prediction market arbitrage opportunity:
            Event: {event_name}
            Action: {action}
            Details: {opp_details}
            System Confidence: {confidence}

            Provide a concise 'Agent Reasoning' (max 2 sentences) explaining why this trade makes sense from a market perspective, considering potential sentiment or volatility on the BNB Chain.
            """
            
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert crypto arbitrage AI agent."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"LLM Reasoning unavailable: {str(e)}"
