import random
import logging
from ..models import ExchangePrice, AIActivityLog

logger = logging.getLogger(__name__)

class ArbitrageService:
    """
    Monitors cross-platform price spreads and identifies execution opportunities.
    """

    EXCHANGES = ["PancakeSwap", "BiSwap", "ApeSwap", "BabyDogeSwap"]
    SYMBOL = "BNB/USDT"

    @staticmethod
    def update_prices():
        """
        Updates exchange prices with 1-2% deviation to create arbitrage spreads.
        """
        base_price = 580.0 # Hypothetical base
        
        for name in ArbitrageService.EXCHANGES:
            # Create artificial price spreads (random walk from base)
            price = base_price * (1 + random.uniform(-0.015, 0.015))
            
            p, created = ExchangePrice.objects.get_or_create(
                exchange_name=name,
                symbol=ArbitrageService.SYMBOL,
                defaults={'price': price}
            )
            p.price = price
            p.save()

    @staticmethod
    def get_monitoring_data():
        """
        Returns latest exchange prices and spreads for the dashboard.
        """
        ArbitrageService.update_prices()
        prices = ExchangePrice.objects.filter(symbol=ArbitrageService.SYMBOL)
        
        return [{
            "platform": p.exchange_name,
            "price": round(p.price, 2),
            "timestamp": p.timestamp.strftime("%H:%M:%S")
        } for p in prices]

    @staticmethod
    def find_spread_opportunity(threshold=1.5):
        """
        Finds the highest spread between any two exchanges.
        If spread > threshold%, trigger arbitrage instruction.
        """
        prices = list(ExchangePrice.objects.filter(symbol=ArbitrageService.SYMBOL))
        if len(prices) < 2: return None
        
        prices.sort(key=lambda x: x.price)
        
        cheap = prices[0]  # Lowest price
        dear = prices[-1]  # Highest price
        
        spread = ((dear.price - cheap.price) / cheap.price) * 100
        
        if spread > threshold:
            return {
                "opportunity": True,
                "buy_on": cheap.exchange_name,
                "sell_on": dear.exchange_name,
                "spread_pct": round(spread, 2),
                "profit_est": round(spread * 100, 2), # $100 profit per $10k
                "reason": f"Price spread between {cheap.exchange_name} and {dear.exchange_name} is {spread:.2f}%."
            }
        
        return None
