from dataclasses import dataclass

from trading_bot.data.indicators import closes_from_candles, relative_strength_index
from trading_bot.data.market_data import Candle
from trading_bot.strategy.base_strategy import BaseStrategy, Signal


@dataclass(frozen=True)
class RsiMeanReversionStrategy(BaseStrategy):
    window: int = 14
    oversold_level: float = 30
    overbought_level: float = 70

    def __post_init__(self) -> None:
        if self.window <= 0:
            raise ValueError("RSI window must be greater than zero.")
        if self.oversold_level >= self.overbought_level:
            raise ValueError("Oversold level must be below overbought level.")

    def generate_signal(self, candles: list[Candle]) -> Signal:
        if len(candles) <= self.window:
            return "HOLD"

        rsi = relative_strength_index(closes_from_candles(candles), self.window)
        if rsi <= self.oversold_level:
            return "BUY"
        if rsi >= self.overbought_level:
            return "SELL"
        return "HOLD"
