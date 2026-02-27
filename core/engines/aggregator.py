import asyncio
import random
import os
import json
from pathlib import Path

class MarketDataAggregator:
    """
    Scans multiple prediction market APIs and DEX pools.
    Now fetches from a JSON file for easy integration with Kaggle or APIs later.
    """
    def __init__(self):
        self.data_path = Path(__file__).parent / "market_data.json"

    async def fetch_market_data(self):
        """
        Purely dynamic simulation for demo purposes.
        Generates 3 different scenarios to showcase BUY, SELL, and STOP logic.
        """
        scenarios = [
            {
                "id": "bnb_bull_path",
                "name": "BNB Chain Ecosystem Growth 2026",
                "type": "ARBITRAGE_PROB" # Good for BUY
            },
            {
                "id": "eth_scaling_v3",
                "name": "Ethereum L2 vs BNB Chain Dominance",
                "type": "SELL_SCENARIO"  # High prices everywhere, maybe a sell
            },
            {
                "id": "efficient_market_demo",
                "name": "BTC Stable Convergence",
                "type": "STOP_SCENARIO" # Very tight spreads, no profit
            }
        ]

        events = []
        for scene in scenarios:
            event = {
                "id": scene["id"],
                "name": scene["name"],
                "markets": []
            }

            # Generate 4 markets for each event
            for i in range(4):
                market_name = ["PancakeSwap", "Polymarket", "Azuro", "Binance"][i]
                
                if scene["type"] == "ARBITRAGE_PROB":
                    # Force a wide spread (e.g., 0.45 vs 0.55) to trigger BUY
                    base_yes = 0.50 + random.uniform(-0.1, 0.1)
                elif scene["type"] == "STOP_SCENARIO":
                    # Force very close prices to trigger STOP
                    base_yes = 0.50 + random.uniform(-0.001, 0.001)
                else: 
                    # Random noise
                    base_yes = random.uniform(0.1, 0.9)

                market = {
                    "name": market_name,
                    "yes": round(base_yes, 4),
                    "no": round(1.0 - base_yes, 4),
                    "liquidity": random.randint(5000, 50000)
                }
                event["markets"].append(market)
            
            # To ensure an arbitrage exists in the ARBITRAGE_PROB scenario:
            if scene["type"] == "ARBITRAGE_PROB":
                # Market 0: Very cheap to Buy YES
                event["markets"][0]["yes"] = 0.05 
                event["markets"][0]["no"] = 0.95
                
                # Market 1: Very cheap to Buy NO (means very expensive to buy YES)
                event["markets"][1]["no"] = 0.05 
                event["markets"][1]["yes"] = 0.95 

                # Result: Buying YES on M0 (0.05) + Buying NO on M1 (0.05) = 0.10 Total Cost!
                # 900% profit (0.90 profit on 0.10 investment).
                # Confidence will be near 99%.

            events.append(event)

        return events

    async def get_gas_price(self):
        return random.randint(1, 3) # Mocked Gwei
