from dataclasses import dataclass

from trading_bot.broker.base_broker import BaseBroker, OrderResult
from trading_bot.execution.order_manager import ExecutionRequest, OrderManager
from trading_bot.risk.risk_manager import RiskManager, TradeRiskDecision
from trading_bot.strategy.base_strategy import Signal


@dataclass(frozen=True)
class PaperTradeResult:
    signal: Signal
    risk: TradeRiskDecision | None
    order: OrderResult | None


class PaperTradingEngine:
    def __init__(self, broker: BaseBroker, risk_manager: RiskManager) -> None:
        self.broker = broker
        self.risk_manager = risk_manager
        self.order_manager = OrderManager(broker)

    def execute(
        self,
        symbol: str,
        signal: Signal,
        stop_loss: float,
        requested_quantity: float | None = None,
    ) -> PaperTradeResult:
        if signal == "HOLD":
            return PaperTradeResult(signal=signal, risk=None, order=None)

        price = self.broker.get_price(symbol)
        decision = self.risk_manager.approve_trade(
            balance=self.broker.get_balance(),
            price=price,
            stop_loss=stop_loss,
            requested_quantity=requested_quantity,
        )
        if not decision.approved:
            return PaperTradeResult(signal=signal, risk=decision, order=None)

        order = self.order_manager.execute_signal(
            ExecutionRequest(symbol=symbol, signal=signal, quantity=decision.quantity)
        )
        return PaperTradeResult(signal=signal, risk=decision, order=order)

