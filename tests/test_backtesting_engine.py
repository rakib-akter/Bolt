from datetime import UTC, datetime, timedelta

from trading_bot.backtesting.engine import BacktestEngine
from trading_bot.data.market_data import Candle
from trading_bot.strategy.moving_average_strategy import MovingAverageStrategy


def make_candles(closes: list[float]) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        Candle("AAPL", start + timedelta(days=index), close, close, close, close, 100)
        for index, close in enumerate(closes)
    ]


def test_backtest_engine_returns_equity_and_trades() -> None:
    strategy = MovingAverageStrategy(short_window=2, long_window=3)
    engine = BacktestEngine(strategy=strategy, starting_cash=1000)

    result = engine.run(make_candles([10, 11, 12, 13]), quantity=1)

    assert result.starting_cash == 1000
    assert result.ending_equity >= 1000
    assert len(result.trades) >= 1

