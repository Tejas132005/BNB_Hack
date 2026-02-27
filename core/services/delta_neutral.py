import os
import json
import logging
from ..models import UserPortfolio, TradeExecution, AIActivityLog

logger = logging.getLogger(__name__)

class DeltaNeutralService:
    """
    Manages spot and hedge balancing to maintain a neutral delta.
    """
    
    @staticmethod
    def calculate_delta(wallet_address):
        """
        Calculates current net delta based on real positions.
        """
        try:
            portfolio = UserPortfolio.objects.get(wallet_address=wallet_address)
            
            # Sum up real confirmed trades to get exposure
            trades = TradeExecution.objects.filter(
                wallet_address=wallet_address, 
                status='Confirmed'
            )
            
            spot_val = 0
            hedge_val = 0
            
            for trade in trades:
                # In this demo model: 
                # BUY = Spot Long
                # SELL = Hedge Short (in a real app this would be futures/options)
                if trade.executed_action == 'BUY':
                    spot_val += (trade.amount * trade.executed_price)
                elif trade.executed_action == 'SELL':
                    hedge_val -= (trade.amount * trade.executed_price)
            
            portfolio.spot_exposure = spot_val
            portfolio.hedge_exposure = hedge_val
            portfolio.net_delta = spot_val + hedge_val
            
            # Simple margin/leverage calculation
            total_exposure = abs(spot_val) + abs(hedge_val)
            portfolio.leverage = total_exposure / portfolio.equity if portfolio.equity > 0 else 1.0
            
            portfolio.save()
            return portfolio
            
        except UserPortfolio.DoesNotExist:
            return None

    @staticmethod
    def get_hedge_instruction(wallet_address, threshold=500.0):
        """
        If net delta exceeds threshold ($500), suggest a rebalance trade.
        """
        portfolio = UserPortfolio.objects.filter(wallet_address=wallet_address).first()
        if not portfolio: return None
        
        delta = portfolio.net_delta
        
        if abs(delta) > threshold:
            action = 'SELL' if delta > 0 else 'BUY'
            amount_needed = abs(delta) # In dollar value
            
            return {
                'instruction': 'REBALANCE_NEEDED',
                'action': action,
                'target_value': amount_needed,
                'reason': f"Net delta of ${delta:.2f} exceeds exposure limit."
            }
        
        return None
