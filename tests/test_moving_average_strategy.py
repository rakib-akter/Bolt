from datetime import UTC, datetime, timedelta

from trading_bot.data.market_data import Candle
from trading_bot.strategy.moving_average_strategy import MovingAverageStrategy


def make_candles(closes: list[float]) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        Candle("AAPL", start + timedelta(days=index), close, close, close, close, 100)
        for index, close in enumerate(closes)
    ]


def test_moving_average_strategy_buys_when_short_average_is_above_long() -> None:
    strategy = MovingAverageStrategy(short_window=2, long_window=4)

    assert strategy.generate_signal(make_candles([1, 2, 4, 8])) == "BUY"


def test_moving_average_strategy_sells_when_short_average_is_below_long() -> None:
    strategy = MovingAverageStrategy(short_window=2, long_window=4)

    assert strategy.generate_signal(make_candles([8, 4, 2, 1])) == "SELL"


def test_moving_average_strategy_holds_without_enough_data() -> None:
    strategy = MovingAverageStrategy(short_window=2, long_window=4)

    assert strategy.generate_signal(make_candles([1, 2, 3])) == "HOLD"

