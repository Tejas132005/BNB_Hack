from .strategy import ArbitrageEngine
from .risk import RiskModel
from .llm_client import LLMAnalyzer

class StrategySelectorAI:
    """
    Selects the optimal strategy based on risk-adjusted returns.
    """
    def __init__(self):
        self.arbitrage_engine = ArbitrageEngine()
        self.risk_model = RiskModel()
        self.llm = LLMAnalyzer()

    def generate_signal(self, normalized_data, fair_values):
        signals = []
        
        for i, event in enumerate(normalized_data):
            fair_value = fair_values[i]
            opportunities = self.arbitrage_engine.find_opportunities(event)
            print(f"SELECTOR DEBUG: Found {len(opportunities)} opps for {event['name']}")
            
            for opp in opportunities:
                is_valid = self.risk_model.validate_strategy(opp)
                print(f"SELECTOR DEBUG: Opp valid: {is_valid}")
                if is_valid:
                    # Get action from opportunity
                    action_type = opp.get("action", "BUY")
                    confidence = opp.get("confidence_score", 0.5)
                    spread_val = opp.get("adjusted_spread", 0)
                    profit_val = opp.get("expected_profit", 0)
                    
                    base_reason = (
                        f"Detected {opp['strategy']} ({action_type}) on '{event['name']}'. "
                        f"Spread: {spread_val*100:.2f}% | "
                        f"Est. Profit: ${profit_val:.2f} | "
                        f"Markets: {opp['buy_market']} -> {opp['sell_market']}."
                    )
                    
                    # AI Reflection Phase
                    llm_reason = self.llm.refine_strategy(action_type, event["name"], base_reason, confidence)
                    
                    signals.append({
                        "id": event["id"],
                        "action": action_type,
                        "confidence": confidence,
                        "reason": f"{base_reason} | AI ANALYSIS: {llm_reason}"
                    })
        
        # Sort by confidence and return top signal
        if signals:
            return sorted(signals, key=lambda x: x["confidence"], reverse=True)[0]
        
        return {
            "action": "STOP",
            "confidence": 0.0,
            "reason": "Market Scan Complete. No profitable arbitrage paths (spread > fees) were detected in current liquidity pools. Confidence score is 0 because no action is recommended."
        }
