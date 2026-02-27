import random
import logging
from ..models import YieldSource, YieldAllocation, UserPortfolio

logger = logging.getLogger(__name__)

class YieldRotationService:
    """
    Ranks DeFi protocols and triggers rotation to maintain max yield.
    """

    DEFAULT_SOURCES = [
        {"name": "PancakeSwap V3", "chain": "BNB Chain", "apy": 12.4, "risk": 2.0, "tvl": 450000},
        {"name": "Venus Vault", "chain": "BNB Chain", "apy": 8.1, "risk": 1.5, "tvl": 1500000},
        {"name": "Tranchella", "chain": "BNB Chain", "apy": 15.6, "risk": 3.4, "tvl": 120000},
        {"name": "Uniswap", "chain": "Ethereum", "apy": 4.2, "risk": 1.1, "tvl": 4500000},
        {"name": "GMX", "chain": "Arbitrum", "apy": 11.2, "risk": 2.5, "tvl": 800000}
    ]

    @staticmethod
    def refresh_yield_data():
        """
        In a real app, this would fetch from DefiLlama or a similar API.
        For the hackathon, we apply slight random drift to simulate live data.
        """
        for src in YieldRotationService.DEFAULT_SOURCES:
            source, created = YieldSource.objects.get_or_create(
                protocol_name=src["name"],
                chain=src["chain"],
                defaults={'apy': src["apy"], 'risk_score': src["risk"], 'tvl': src["tvl"]}
            )
            # Simulate dynamic yield fluctuations (+/- 10%)
            drift = random.uniform(0.9, 1.1)
            source.apy = round(src["apy"] * drift, 2)
            source.tvl = round(src["tvl"] * drift)
            source.save()

    @staticmethod
    def get_best_source(risk_tolerance=50):
        """
        Ranks sources based on risk-adjusted yield.
        Formula: yield * (1 - risk/10)
        """
        sources = YieldSource.objects.all()
        if not sources:
            YieldRotationService.refresh_yield_data()
            sources = YieldSource.objects.all()
        
        ranked = []
        for s in sources:
            # Simple risk-adjusted score
            score = s.apy * (1 - (s.risk_score / 10))
            ranked.append((s, score))
        
        # Sort by score descending
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[0][0] if ranked else None

    @staticmethod
    def check_rotation(wallet_address):
        """
        Checks if current allocation is suboptimal.
        If current yield < best yield - 2%, suggest rotation.
        """
        # Ensure data is fresh
        YieldRotationService.refresh_yield_data()
        
        current_alloc = YieldAllocation.objects.filter(wallet_address=wallet_address).first()
        best_source = YieldRotationService.get_best_source()
        
        if not current_alloc:
            return {
                "rotation_needed": True,
                "action": "DEPOSIT",
                "to": best_source.protocol_name,
                "apy": best_source.apy,
                "reason": "Initial capital allocation is required."
            }
        
        if current_alloc.source.id != best_source.id:
            diff = best_source.apy - current_alloc.source.apy
            if diff > 2.0: # 2% yield threshold for rotation
                return {
                    "rotation_needed": True,
                    "action": "ROTATE",
                    "from": current_alloc.source.protocol_name,
                    "to": best_source.protocol_name,
                    "gain": diff,
                    "reason": f"Better opportunity found elsewhere (APY diff: {diff:.1f}%)."
                }
        
        return None
