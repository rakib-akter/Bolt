from dataclasses import dataclass
from typing import Literal

from trading_bot.broker.base_broker import Position
from trading_bot.strategy.base_strategy import Signal

SellAction = Literal["SELL", "HOLD"]


@dataclass(frozen=True)
class SellDecision:
    symbol: str
    action: SellAction
    quantity: float
    reason: str
    current_price: float
    average_price: float
    unrealized_pl_percent: float


@dataclass(frozen=True)
class SellDecisionEngine:
    stop_loss_percent: float = 0.05
    take_profit_percent: float = 0.10

    def evaluate(
        self,
        position: Position,
        current_price: float,
        strategy_signal: Signal,
    ) -> SellDecision:
        average_price = position.average_price
        pl_percent = (current_price - average_price) / average_price

        if pl_percent <= -self.stop_loss_percent:
            return SellDecision(
                symbol=position.symbol,
                action="SELL",
                quantity=position.quantity,
                reason="Stop loss reached.",
                current_price=current_price,
                average_price=average_price,
                unrealized_pl_percent=pl_percent,
            )

        if pl_percent >= self.take_profit_percent:
            return SellDecision(
                symbol=position.symbol,
                action="SELL",
                quantity=position.quantity,
                reason="Take profit reached.",
                current_price=current_price,
                average_price=average_price,
                unrealized_pl_percent=pl_percent,
            )

        if strategy_signal == "SELL":
            return SellDecision(
                symbol=position.symbol,
                action="SELL",
                quantity=position.quantity,
                reason="Strategy generated a sell signal.",
                current_price=current_price,
                average_price=average_price,
                unrealized_pl_percent=pl_percent,
            )

        return SellDecision(
            symbol=position.symbol,
            action="HOLD",
            quantity=0,
            reason="No sell rule triggered.",
            current_price=current_price,
            average_price=average_price,
            unrealized_pl_percent=pl_percent,
        )

