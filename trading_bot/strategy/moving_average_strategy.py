from dataclasses import dataclass

from trading_bot.data.indicators import closes_from_candles, simple_moving_average
from trading_bot.data.market_data import Candle
from trading_bot.strategy.base_strategy import BaseStrategy, Signal


@dataclass(frozen=True)
class MovingAverageStrategy(BaseStrategy):
    short_window: int = 5
    long_window: int = 20

    def __post_init__(self) -> None:
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("Moving average windows must be greater than zero.")
        if self.short_window >= self.long_window:
            raise ValueError("Short window must be smaller than long window.")

    def generate_signal(self, candles: list[Candle]) -> Signal:
        if len(candles) < self.long_window:
            return "HOLD"

        closes = closes_from_candles(candles)
        short_ma = simple_moving_average(closes, self.short_window)
        long_ma = simple_moving_average(closes, self.long_window)

        if short_ma > long_ma:
            return "BUY"
        if short_ma < long_ma:
            return "SELL"
        return "HOLD"

