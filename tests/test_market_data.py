from datetime import UTC, datetime

import pytest

from trading_bot.data.indicators import simple_moving_average
from trading_bot.data.market_data import Candle, MarketDataStore


def test_market_store_returns_latest_price_from_sorted_candles() -> None:
    store = MarketDataStore()
    store.add_candle(Candle("AAPL", datetime(2026, 1, 2, tzinfo=UTC), 10, 12, 9, 11, 100))
    store.add_candle(Candle("AAPL", datetime(2026, 1, 1, tzinfo=UTC), 8, 10, 7, 9, 100))

    assert store.latest_price("aapl") == 11


def test_candle_requires_timezone() -> None:
    with pytest.raises(ValueError):
        Candle("AAPL", datetime(2026, 1, 1), 10, 12, 9, 11, 100)


def test_simple_moving_average_uses_trailing_window() -> None:
    assert simple_moving_average([1, 2, 3, 4], 2) == 3.5

