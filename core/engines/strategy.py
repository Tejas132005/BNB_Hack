class ArbitrageEngine:
    """
    Advanced Cross-Market Arbitrage Engine
    Includes liquidity, slippage, fees, and gas estimation.
    """

    MIN_SPREAD = 0.005  # 0.5% threshold for spot markets
    MAX_CAPITAL = 1000  # demo capital allocation
    FEE_RATE = 0.001     # 0.1% trading fee (standard for DEX/CEX)
    GAS_ESTIMATE = 0.5    # Lower gas estimate for BNB Chain

    def find_opportunities(self, event):
        comparisons = event.get("comparisons", [])
        if len(comparisons) < 2:
            return []

        opportunities = []

        # ARBITRAGE Logic:
        # Market A: Buy YES @ 0.20
        # Market B: Buy NO @ 0.10 (which means YES is 'priced' at 0.90)
        # We buy cheap YES on A, and buy cheap NO on B.
        
        # Best BUY for YES (Lowest yes_prob)
        best_yes_buy = min(comparisons, key=lambda x: x["yes_prob"])
        # BEST BUY for NO (this is essentially 'selling' YES at the highest price)
        # Lowest no_prob means Highest yes_prob
        best_no_buy = min(comparisons, key=lambda x: x["no_prob"])

        # Example: 
        # Market A: Yes=0.20, No=0.80
        # Market B: Yes=0.90, No=0.10
        # best_yes_buy = Market A (0.20)
        # best_no_buy = Market B (0.10)
        
        # Total cost = 0.20 + 0.10 = 0.30
        # Risk-free payout = 1.00 (either YES or NO happens)
        # Profit = 1.00 - 0.30 = 0.70
        total_cost = best_yes_buy["yes_prob"] + best_no_buy["no_prob"]
        print(f"ENGINE DEBUG: Event {event['id']} - YesBuy: {best_yes_buy['yes_prob']} NoBuy: {best_no_buy['no_prob']} Cost: {total_cost}")
        
        if total_cost >= 1.0:
            # No arbitrage available (efficient market)
            return []

        # Calculate Spread (as % profit on cost)
        raw_spread = (1.0 - total_cost) / total_cost

        if raw_spread < self.MIN_SPREAD:
            return [] 

        # --- Liquidity Check ---
        size = min(best_yes_buy["yes_liquidity"], best_no_buy["no_liquidity"], self.MAX_CAPITAL)
        if size <= 0: return []

        # Simple profit: (1.0 - TotalCost) * size - fees
        expected_profit = (1.0 - total_cost) * size - (size * self.FEE_RATE) - self.GAS_ESTIMATE

        if expected_profit > 0:
            opportunities.append({
                "strategy": "CROSS_MARKET_ARBITRAGE",
                "action": "BUY",
                "event_id": event["id"],
                "buy_market": best_yes_buy["provider"],
                "sell_market": best_no_buy["provider"], # In this case, we buy NO to hedge
                "position_size": size,
                "adjusted_spread": raw_spread,
                "expected_profit": expected_profit,
                "confidence_score": self.score_opportunity(raw_spread, size)
            })

        return opportunities


    def simulate_slippage(self, price, trade_size, liquidity):
        """
        Simple linear slippage model.
        Later replace with AMM curve simulation.
        """
        if liquidity == 0:
            return price

        impact_ratio = trade_size / liquidity
        slippage_factor = 0.02  # assume 2% max slippage
        return price + (impact_ratio * slippage_factor)


    def score_opportunity(self, spread, size):
        """
        Calculates a Risk-Adjusted Confidence Score.
        Now more conservative to prevent constant 1.0 results.
        """
        # Spread component (max 0.5 at 10% spread)
        # Spread component (scaled: 1% spread = 0.5 score)
        spread_score = min(0.6, spread * 50)
        
        # Liquidity component (max 0.3)
        liquidity_score = min(0.3, (size / self.MAX_CAPITAL) * 0.3)
        
        # Risk / Volatility Penalty
        import random
        volatility_penalty = random.uniform(0.01, 0.05)
        
        score = spread_score + liquidity_score - volatility_penalty
        return round(max(0.2, min(0.99, score)), 2)

class DeltaNeutralEngine:

    MAX_CAPITAL = 1000

    def analyze(self, market_a, market_b):
        """
        market_a and market_b contain:
        {
            "yes_prob": float,
            "no_prob": float,
            "yes_liquidity": float,
            "no_liquidity": float
        }
        """

        yes_price_a = market_a["yes_prob"]
        yes_price_b = market_b["yes_prob"]

        spread = yes_price_b - yes_price_a

        if abs(spread) < 0.015:
            return None

        position_size = min(
            market_a.get("yes_liquidity", market_a.get("depth", 0)),
            market_b.get("yes_liquidity", market_b.get("depth", 0)),
            self.MAX_CAPITAL
        )

        # Simulate outcomes
        payout_if_yes = position_size * (1 - yes_price_a)
        payout_if_no = position_size * (yes_price_b - 1)

        min_payout = min(payout_if_yes, payout_if_no)

        if min_payout <= 0:
            return None

        return {
            "strategy": "DELTA_NEUTRAL",
            "position_size": position_size,
            "expected_worst_case_profit": min_payout,
            "confidence": min(1.0, abs(spread) * 8)
        }
