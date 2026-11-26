"""Data Collection Package Initializer and Provider Factory."""
from config.settings import settings
from src.data_collection.base_provider import BaseDataProvider
from src.data_collection.yfinance_provider import YahooFinanceProvider
from src.data_collection.invezgo_provider import InvezgoProvider
from src.data_collection.apicoid_provider import ApiCoIdProvider
from src.data_collection.mock_provider import MockDataProvider
from src.data_collection.universe_manager import UniverseManager


def get_data_provider(provider_name: str = None) -> BaseDataProvider:
    """Factory function to instantiate configured market data provider."""
    target = (provider_name or settings.DEFAULT_DATA_PROVIDER).lower().strip()
    
    if target == "invezgo":
        return InvezgoProvider()
    elif target == "apicoid":
        return ApiCoIdProvider()
    elif target == "mock":
        return MockDataProvider()
    else:
        return YahooFinanceProvider()


__all__ = [
    "BaseDataProvider",
    "YahooFinanceProvider",
    "InvezgoProvider",
    "ApiCoIdProvider",
    "MockDataProvider",
    "UniverseManager",
    "get_data_provider",
]
