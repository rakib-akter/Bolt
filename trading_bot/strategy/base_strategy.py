from abc import ABC, abstractmethod
from typing import Literal

from trading_bot.data.market_data import Candle

Signal = Literal["BUY", "SELL", "HOLD"]


class BaseStrategy(ABC):
    @abstractmethod
    def generate_signal(self, candles: list[Candle]) -> Signal:
        raise NotImplementedError

