from datetime import UTC, datetime, timedelta

from trading_bot.data.market_data import Candle
from trading_bot.strategy.registry import STRATEGIES, create_strategy


def make_candles(closes: list[float]) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        Candle("AAPL", start + timedelta(days=index), close, close, close, close, 1000)
        for index, close in enumerate(closes)
    ]


def test_strategy_registry_creates_all_available_strategies() -> None:
    candles = make_candles([100, 101, 102, 103, 104, 110, 115, 120, 124, 128] * 3)

    for strategy_id in STRATEGIES:
        strategy = create_strategy(strategy_id)
        signal = strategy.generate_signal(candles)
        assert signal in {"BUY", "SELL", "HOLD"}
