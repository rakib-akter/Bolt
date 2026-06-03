from dataclasses import dataclass

from trading_bot.broker.base_broker import BaseBroker, OrderResult
from trading_bot.strategy.base_strategy import Signal


@dataclass(frozen=True)
class ExecutionRequest:
    symbol: str
    signal: Signal
    quantity: float


class OrderManager:
    def __init__(self, broker: BaseBroker) -> None:
        self.broker = broker
        self._last_signal_by_symbol: dict[str, Signal] = {}

    def execute_signal(self, request: ExecutionRequest) -> OrderResult | None:
        symbol = request.symbol.upper()
        if request.signal == "HOLD":
            self._last_signal_by_symbol[symbol] = request.signal
            return None
        if request.quantity <= 0:
            return OrderResult(symbol, "buy", request.quantity, 0, "rejected", "Bad quantity.")
        if self._last_signal_by_symbol.get(symbol) == request.signal:
            return OrderResult(
                symbol,
                "buy" if request.signal == "BUY" else "sell",
                request.quantity,
                0,
                "rejected",
                "Duplicate signal blocked.",
            )

        side = "buy" if request.signal == "BUY" else "sell"
        result = self.broker.place_order(symbol, side, request.quantity)
        if result.status == "filled":
            self._last_signal_by_symbol[symbol] = request.signal
        return result

