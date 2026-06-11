from dataclasses import dataclass

from trading_bot.data.indicators import closes_from_candles
from trading_bot.data.market_data import Candle
from trading_bot.strategy.base_strategy import BaseStrategy, Signal


@dataclass(frozen=True)
class MomentumStrategy(BaseStrategy):
    lookback: int = 5
    threshold_percent: float = 0.02

    def __post_init__(self) -> None:
        if self.lookback <= 0:
            raise ValueError("Lookback must be greater than zero.")
        if self.threshold_percent <= 0:
            raise ValueError("Threshold percent must be greater than zero.")

    def generate_signal(self, candles: list[Candle]) -> Signal:
        if len(candles) <= self.lookback:
            return "HOLD"

        closes = closes_from_candles(candles)
        previous = closes[-self.lookback - 1]
        latest = closes[-1]
        move_percent = (latest - previous) / previous

        if move_percent >= self.threshold_percent:
            return "BUY"
        if move_percent <= -self.threshold_percent:
            return "SELL"
        return "HOLD"
