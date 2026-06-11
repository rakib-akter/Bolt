from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class Candle:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("Candle timestamp must include timezone information.")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("Candle prices must be greater than zero.")
        if self.low > self.high:
            raise ValueError("Candle low cannot be greater than high.")
        if self.volume < 0:
            raise ValueError("Candle volume cannot be negative.")


class MarketDataStore:
    def __init__(self) -> None:
        self._candles: dict[str, list[Candle]] = {}

    def add_candle(self, candle: Candle) -> None:
        symbol = candle.symbol.upper()
        candles = self._candles.setdefault(symbol, [])
        candles.append(candle)
        candles.sort(key=lambda item: item.timestamp)

    def latest_price(self, symbol: str) -> float:
        candles = self.candles_for(symbol)
        if not candles:
            raise KeyError(f"No candles available for {symbol.upper()}.")
        return candles[-1].close

    def candles_for(self, symbol: str) -> list[Candle]:
        return list(self._candles.get(symbol.upper(), []))

    def clear(self) -> None:
        self._candles.clear()


def utc_now() -> datetime:
    return datetime.now(UTC)
