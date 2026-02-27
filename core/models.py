from django.db import models
from django.contrib.auth.models import User

class Strategy(models.Model):
    STRATEGY_TYPES = [
        ('CONSERVATIVE', 'Conservative (Stablecoin Arbitrage)'),
        ('MODERATE', 'Moderate (Funding Rate Delta-Neutral)'),
        ('AGGRESSIVE', 'Aggressive (Cross-Chain Yield Rotation)'),
    ]
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=STRATEGY_TYPES)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.type})"

class AIActivityLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=50) # e.g., 'Arbitrage', 'Rebalance', 'Hedge'
    message = models.TextField()
    reasoning = models.TextField(blank=True, null=True)
    confidence_score = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.timestamp} - {self.event_type}"


class UserPortfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    wallet_address = models.CharField(max_length=255, unique=True, db_index=True, default='0x0')
    total_deposited = models.FloatField(default=10000.0)
    current_balance = models.FloatField(default=10000.0)
    active_strategy = models.ForeignKey(Strategy, on_delete=models.SET_NULL, null=True, blank=True)
    risk_tolerance = models.IntegerField(default=50) # 0-100
    
    # Delta-Neutral Fields
    spot_exposure = models.FloatField(default=0)
    hedge_exposure = models.FloatField(default=0)
    net_delta = models.FloatField(default=0)
    equity = models.FloatField(default=10000.0)
    
    # Risk Metrics
    leverage = models.FloatField(default=1.0)
    max_drawdown = models.FloatField(default=0.0)
    sharpe_ratio = models.FloatField(default=0.0)
    
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Portfolio: {self.wallet_address[:10]}..."

class YieldSource(models.Model):
    protocol_name = models.CharField(max_length=255)
    chain = models.CharField(max_length=50)
    apy = models.FloatField()
    risk_score = models.FloatField()
    tvl = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

class YieldAllocation(models.Model):
    wallet_address = models.CharField(max_length=255, db_index=True)
    source = models.ForeignKey(YieldSource, on_delete=models.CASCADE)
    allocated_amount = models.FloatField()

class ExchangePrice(models.Model):
    exchange_name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=50)
    price = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)

class TradeLog(models.Model):
    wallet_address = models.CharField(max_length=255, db_index=True)
    strategy_type = models.CharField(max_length=100) # ARBITRAGE, DELTA_NEUTRAL, YIELD_ROTATION
    entry_price = models.FloatField()
    exit_price = models.FloatField(null=True)
    size = models.FloatField()
    pnl = models.FloatField(default=0)
    fees = models.FloatField(default=0)
    tx_hash = models.CharField(max_length=255, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class TradeExecution(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    signal = models.CharField(max_length=50)
    executed_action = models.CharField(max_length=20) # BUY, SELL, STOP
    price = models.FloatField()
    executed_price = models.FloatField(null=True, blank=True)
    amount = models.FloatField() # Quantity
    tx_hash = models.CharField(max_length=255, null=True, blank=True)
    block_number = models.IntegerField(null=True, blank=True)
    gas_fee = models.FloatField(null=True, blank=True)
    chain = models.CharField(max_length=50, default='BNB Chain')
    wallet_address = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    confidence = models.FloatField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.executed_action} @ {self.executed_price} ({self.status}) - {self.timestamp}"