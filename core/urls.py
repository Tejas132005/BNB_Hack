from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (StrategyViewSet, AIActivityLogViewSet, UserPortfolioViewSet, 
                    ArbitrageAPI, AIViewSet, MarketScannerAPI, dashboard, landing, scanner)

router = DefaultRouter()
router.register(r'strategies', StrategyViewSet)
router.register(r'ai-logs', AIActivityLogViewSet)
router.register(r'portfolio', UserPortfolioViewSet)
router.register(r'agent', ArbitrageAPI, basename='agent')
router.register(r'ai', AIViewSet, basename='ai')
router.register(r'scanner', MarketScannerAPI, basename='scanner')

urlpatterns = [
    path('', landing, name='landing'),
    path('dashboard/', dashboard, name='dashboard'),
    path('scanner/', scanner, name='scanner'),
    path('api/', include(router.urls)),
]
