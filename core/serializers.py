from rest_framework import serializers
from .models import (Strategy, AIActivityLog, UserPortfolio, TradeExecution, 
                    TradeLog, YieldSource, YieldAllocation, ExchangePrice)

class StrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = Strategy
        fields = '__all__'

class AIActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIActivityLog
        fields = '__all__'

class UserPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPortfolio
        fields = '__all__'

class TradeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeLog
        fields = '__all__'

class TradeExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeExecution
        fields = '__all__'
