from dataclasses import dataclass

from trading_bot.data.market_data import Candle
from trading_bot.strategy.base_strategy import BaseStrategy, Signal


@dataclass(frozen=True)
class BreakoutStrategy(BaseStrategy):
    lookback: int = 20

    def __post_init__(self) -> None:
        if self.lookback <= 1:
            raise ValueError("Lookback must be greater than one.")

    def generate_signal(self, candles: list[Candle]) -> Signal:
        if len(candles) <= self.lookback:
            return "HOLD"

        history = candles[-self.lookback - 1 : -1]
        latest = candles[-1]
        resistance = max(candle.high for candle in history)
        support = min(candle.low for candle in history)

        if latest.close > resistance:
            return "BUY"
        if latest.close < support:
            return "SELL"
        return "HOLD"
