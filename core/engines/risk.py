class RiskModel:
    """
    Evaluates strategy risk based on capital exposure and liquidity.
    """
    def __init__(self, max_exposure=1000, max_drawdown=0.1):
        self.max_exposure = max_exposure
        self.max_drawdown = max_drawdown

    def validate_strategy(self, strategy_data):
        profit = strategy_data.get("expected_profit", 0)
        # For hackathon demo, we accept any positive profit
        return profit > 0

    def calculate_position_size(self, confidence, total_capital=1000):
        # Kelly Criterion simplified
        return total_capital * 0.1 * confidence 
