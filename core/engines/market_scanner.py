"""
AI Market Scanner Engine
Generates dynamic market data, performs technical analysis,
and produces trading signals with confidence scores.
"""
import random
import math
import time
import hashlib
import uuid
from datetime import datetime, timedelta


class MarketDataEngine:
    """
    Generates 100 rows of realistic market data using random walk logic
    with volatility shifts. Refreshes entirely every cycle.
    """

    def __init__(self):
        self.base_price = 580.0 + random.uniform(-20, 20)
        self.base_volume = 1500000
        self.rsi = 50.0
        self.macd = 0.0
        self.volatility = 0.02
        self.funding_rate = 0.0001
        self._last_generated = None
        self._cached_data = None

    def generate_dataset(self, rows=100):
        """
        Generate a full dataset of `rows` market data points.
        Uses random walk with momentum, mean reversion, and volatility clustering.
        """
        data = []
        price = self.base_price + random.uniform(-10, 10)
        volume = self.base_volume
        rsi = 50.0 + random.uniform(-10, 10)
        macd = random.uniform(-2, 2)
        volatility = self.volatility + random.uniform(-0.005, 0.005)
        funding_rate = self.funding_rate

        now = datetime.now()

        # Trend bias for this cycle
        trend_bias = random.choice([-1, 0, 0, 1]) * random.uniform(0.0001, 0.0005)

        for i in range(rows):
            # Timestamp: spread across last ~16 minutes (10s intervals)
            ts = now - timedelta(seconds=(rows - i) * 10)

            # Random walk with momentum + mean reversion
            momentum = random.gauss(trend_bias, volatility)
            price_change = price * momentum
            price = max(price + price_change, 100)  # Floor at 100

            # Volume: correlated with abs price change, no longer compounding exponentially
            vol_spike = 1.0 + abs(momentum) * 100
            volume = max(50000, self.base_volume * random.uniform(0.6, 1.4) * vol_spike)

            # RSI: bounded [0, 100], mean-reverting around 50
            rsi_drift = random.gauss(0, 3)
            if rsi > 70:
                rsi_drift -= 2
            elif rsi < 30:
                rsi_drift += 2
            rsi = max(0, min(100, rsi + rsi_drift))

            # MACD: slight random walk
            macd += random.gauss(0, 0.3)
            macd = max(-10, min(10, macd))

            # Volatility: clustering (GARCH-like)
            vol_shock = random.gauss(0, 0.003)
            volatility = max(0.005, min(0.08, volatility * 0.95 + abs(vol_shock) + 0.001))

            # Funding rate: slight drift
            funding_rate += random.gauss(0, 0.00005)
            funding_rate = max(-0.001, min(0.003, funding_rate))

            data.append({
                'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'price': round(price, 2),
                'volume': round(volume, 0),
                'rsi': round(rsi, 2),
                'macd': round(macd, 4),
                'volatility': round(volatility, 6),
                'funding_rate': round(funding_rate, 6),
            })

        # Update base for next cycle
        self.base_price = price
        self.rsi = rsi
        self.macd = macd
        self.volatility = volatility
        self.funding_rate = funding_rate

        self._cached_data = data
        self._last_generated = time.time()

        return data

    def get_cached_or_generate(self, max_age=10):
        """Return cached data if fresh, else regenerate."""
        if self._cached_data and self._last_generated:
            age = time.time() - self._last_generated
            if age < max_age:
                return self._cached_data
        return self.generate_dataset()


class MarketAnalyzer:
    """
    Analyzes market data using rule-based + AI logic to produce trading signals.
    """

    @staticmethod
    def analyze(dataset):
        """
        Analyze the 100-row dataset to produce a signal.
        Returns: { signal, confidence, riskLevel }
        """
        if not dataset or len(dataset) < 10:
            return {
                'signal': 'STOP',
                'confidence': 0,
                'riskLevel': 'High',
            }

        # Extract latest values
        latest = dataset[-1]
        prices = [row['price'] for row in dataset]
        rsis = [row['rsi'] for row in dataset]
        macds = [row['macd'] for row in dataset]
        vols = [row['volatility'] for row in dataset]
        funding_rates = [row['funding_rate'] for row in dataset]

        # --- Technical Indicators ---
        current_price = prices[-1]
        avg_price_20 = sum(prices[-20:]) / min(20, len(prices[-20:]))
        avg_price_50 = sum(prices[-50:]) / min(50, len(prices[-50:]))
        current_rsi = rsis[-1]
        avg_rsi = sum(rsis[-10:]) / 10
        current_macd = macds[-1]
        prev_macd = macds[-5] if len(macds) >= 5 else macds[0]
        avg_vol = sum(vols[-10:]) / 10
        current_vol = vols[-1]
        avg_funding = sum(funding_rates[-10:]) / 10

        # --- Scoring System ---
        score = 0  # Positive = BUY bias, negative = SELL bias
        confidence_factors = []

        # 1. RSI Analysis
        if current_rsi < 30:
            score += 3
            confidence_factors.append(('RSI oversold', 15))
        elif current_rsi < 40:
            score += 1.5
            confidence_factors.append(('RSI approaching oversold', 8))
        elif current_rsi > 70:
            score -= 3
            confidence_factors.append(('RSI overbought', 15))
        elif current_rsi > 60:
            score -= 1.5
            confidence_factors.append(('RSI approaching overbought', 8))
        else:
            confidence_factors.append(('RSI neutral', 3))

        # 2. MACD Crossover
        if current_macd > 0 and prev_macd <= 0:
            score += 2.5
            confidence_factors.append(('MACD bullish crossover', 12))
        elif current_macd < 0 and prev_macd >= 0:
            score -= 2.5
            confidence_factors.append(('MACD bearish crossover', 12))
        elif current_macd > prev_macd:
            score += 1
            confidence_factors.append(('MACD rising', 5))
        else:
            score -= 1
            confidence_factors.append(('MACD declining', 5))

        # 3. Price vs Moving Averages
        if current_price > avg_price_20 > avg_price_50:
            score += 2
            confidence_factors.append(('Bullish MA alignment', 10))
        elif current_price < avg_price_20 < avg_price_50:
            score -= 2
            confidence_factors.append(('Bearish MA alignment', 10))

        # 4. Volatility Assessment
        if current_vol > avg_vol * 1.5:
            # High volatility → reduce confidence, suggest LIMIT
            confidence_factors.append(('High volatility spike', -8))
        elif current_vol < avg_vol * 0.7:
            confidence_factors.append(('Low volatility environment', 5))

        # 5. Funding Rate
        if avg_funding > 0.001:
            score -= 1  # Overcrowded long
            confidence_factors.append(('High funding rate', 5))
        elif avg_funding < -0.0005:
            score += 1  # Overcrowded short
            confidence_factors.append(('Negative funding rate', 5))

        # 6. Price Momentum (last 10 ticks)
        price_change_pct = ((prices[-1] - prices[-10]) / prices[-10]) * 100 if len(prices) >= 10 else 0
        if price_change_pct > 1:
            score += 1.5
            confidence_factors.append(('Strong upward momentum', 8))
        elif price_change_pct < -1:
            score -= 1.5
            confidence_factors.append(('Strong downward momentum', 8))

        # --- Determine Signal ---
        total_confidence_boost = sum(f[1] for f in confidence_factors)
        base_confidence = 50 + total_confidence_boost
        base_confidence = max(20, min(95, base_confidence))

        # Add some controlled randomness
        base_confidence += random.uniform(-5, 5)
        base_confidence = max(15, min(98, base_confidence))

        if current_vol > avg_vol * 2:
            signal = 'LIMIT'
            risk_level = 'High'
            base_confidence = min(base_confidence, 65)
        elif abs(score) < 1.5:
            signal = 'STOP'
            risk_level = 'Low'
            base_confidence = min(base_confidence, 50)
        elif score >= 1.5:
            signal = 'BUY'
            risk_level = 'Low' if score > 4 else 'Moderate'
        else:
            signal = 'SELL'
            risk_level = 'Low' if score < -4 else 'Moderate'

        return {
            'signal': signal,
            'confidence': round(base_confidence),
            'riskLevel': risk_level,
            'score': round(score, 2),
            'factors': [f[0] for f in confidence_factors],
        }


class BNBTradeExecutor:
    """
    Simulates trade execution on BNB Chain.
    Generates mock transaction hashes and confirmation responses.
    """

    @staticmethod
    def execute_trade(action, price, amount=1.0):
        """
        Simulate BNB Chain trade execution.
        Returns a mock transaction result after simulated latency.
        """
        # Simulate execution latency (1-2 sec in real async, instant here for sync)
        tx_hash = '0x' + hashlib.sha256(
            f"{action}-{price}-{time.time()}-{uuid.uuid4()}".encode()
        ).hexdigest()[:64]

        block_number = random.randint(35000000, 40000000)
        gas_used = random.randint(21000, 150000)
        gas_price_gwei = round(random.uniform(3, 8), 2)
        gas_fee_bnb = round((gas_used * gas_price_gwei) / 1e9, 8)

        # Simulate slight slippage
        slippage = random.uniform(-0.002, 0.002)
        executed_price = round(price * (1 + slippage), 2)

        return {
            'success': True,
            'action': action,
            'chain': 'BNB Chain',
            'network': 'BSC Testnet',
            'tx_hash': tx_hash,
            'block_number': block_number,
            'gas_used': gas_used,
            'gas_price_gwei': gas_price_gwei,
            'gas_fee_bnb': gas_fee_bnb,
            'requested_price': price,
            'executed_price': executed_price,
            'slippage_pct': round(slippage * 100, 4),
            'amount': amount,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Confirmed',
            'confirmations': random.randint(1, 15),
        }

    @staticmethod
    def get_summary_for_llm(dataset):
        """
        Create a compact summary of the dataset suitable for LLM analysis.
        """
        if not dataset:
            return "No data available."

        prices = [r['price'] for r in dataset]
        rsis = [r['rsi'] for r in dataset]
        macds = [r['macd'] for r in dataset]
        vols = [r['volatility'] for r in dataset]
        frs = [r['funding_rate'] for r in dataset]

        latest = dataset[-1]
        earliest = dataset[0]

        price_change = ((latest['price'] - earliest['price']) / earliest['price']) * 100

        summary = (
            f"Market Data Summary (Last {len(dataset)} ticks):\n"
            f"- Time Range: {earliest['timestamp']} to {latest['timestamp']}\n"
            f"- Price: Current={latest['price']}, High={max(prices)}, Low={min(prices)}, "
            f"Avg={round(sum(prices)/len(prices), 2)}, Change={round(price_change, 2)}%\n"
            f"- RSI: Current={latest['rsi']}, Avg={round(sum(rsis)/len(rsis), 2)}, "
            f"Min={round(min(rsis), 2)}, Max={round(max(rsis), 2)}\n"
            f"- MACD: Current={latest['macd']}, Avg={round(sum(macds)/len(macds), 4)}\n"
            f"- Volatility: Current={latest['volatility']}, Avg={round(sum(vols)/len(vols), 6)}\n"
            f"- Funding Rate: Current={latest['funding_rate']}, Avg={round(sum(frs)/len(frs), 6)}\n"
            f"- Volume: Current={latest['volume']}, Avg={round(sum(r['volume'] for r in dataset)/len(dataset), 0)}\n"
        )
        return summary


# Singleton instance for consistent state across requests
_engine_instance = None

def get_market_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = MarketDataEngine()
    return _engine_instance
