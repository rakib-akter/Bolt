from dataclasses import dataclass

from trading_bot.broker.base_broker import BaseBroker, Position


@dataclass(frozen=True)
class PositionSnapshot:
    symbol: str
    quantity: float
    average_price: float
    market_price: float
    market_value: float
    unrealized_pl: float


@dataclass(frozen=True)
class PortfolioSnapshot:
    cash: float
    positions: list[PositionSnapshot]
    total_market_value: float
    total_unrealized_pl: float
    total_equity: float


class PortfolioManager:
    def __init__(self, broker: BaseBroker) -> None:
        self.broker = broker

    def snapshot(self) -> PortfolioSnapshot:
        cash = self.broker.get_balance()
        position_snapshots = [self._snapshot_position(item) for item in self.broker.get_positions()]
        total_market_value = sum(item.market_value for item in position_snapshots)
        total_unrealized_pl = sum(item.unrealized_pl for item in position_snapshots)
        return PortfolioSnapshot(
            cash=cash,
            positions=position_snapshots,
            total_market_value=total_market_value,
            total_unrealized_pl=total_unrealized_pl,
            total_equity=cash + total_market_value,
        )

    def _snapshot_position(self, position: Position) -> PositionSnapshot:
        market_price = self.broker.get_price(position.symbol)
        market_value = market_price * position.quantity
        cost_basis = position.average_price * position.quantity
        return PositionSnapshot(
            symbol=position.symbol,
            quantity=position.quantity,
            average_price=position.average_price,
            market_price=market_price,
            market_value=market_value,
            unrealized_pl=market_value - cost_basis,
        )

