from dataclasses import dataclass, field
from datetime import UTC, datetime

from trading_bot.broker.base_broker import BaseBroker, OrderResult
from trading_bot.data.market_data import MarketDataStore
from trading_bot.execution.paper_trading import PaperTradingEngine
from trading_bot.strategy.moving_average_strategy import MovingAverageStrategy
from trading_bot.strategy.sell_decision import SellDecisionEngine


@dataclass
class AutopilotState:
    enabled: bool = False
    mode: str = "paper"
    symbols: list[str] = field(default_factory=lambda: ["AAPL", "MSFT", "NVDA", "TSLA", "SPY"])
    auto_sell_enabled: bool = True
    stop_loss_percent: float = 0.05
    take_profit_percent: float = 0.10
    last_action: str = "Autopilot is off."
    last_run_at: datetime | None = None
    orders: list[OrderResult] = field(default_factory=list)


class PaperAutopilot:
    def __init__(
        self,
        broker: BaseBroker,
        market_data: MarketDataStore,
        strategy: MovingAverageStrategy,
        trading_engine: PaperTradingEngine,
        sell_decision_engine: SellDecisionEngine,
    ) -> None:
        self.broker = broker
        self.market_data = market_data
        self.strategy = strategy
        self.trading_engine = trading_engine
        self.sell_decision_engine = sell_decision_engine
        self.state = AutopilotState()

    def configure_auto_sell(
        self,
        auto_sell_enabled: bool | None = None,
        stop_loss_percent: float | None = None,
        take_profit_percent: float | None = None,
    ) -> AutopilotState:
        if auto_sell_enabled is not None:
            self.state.auto_sell_enabled = auto_sell_enabled
        if stop_loss_percent is not None:
            if stop_loss_percent <= 0:
                raise ValueError("Stop loss percent must be greater than zero.")
            self.state.stop_loss_percent = stop_loss_percent
        if take_profit_percent is not None:
            if take_profit_percent <= 0:
                raise ValueError("Take profit percent must be greater than zero.")
            self.state.take_profit_percent = take_profit_percent

        self.sell_decision_engine = SellDecisionEngine(
            stop_loss_percent=self.state.stop_loss_percent,
            take_profit_percent=self.state.take_profit_percent,
        )
        self.state.last_action = "Auto-sell rules updated."
        return self.state

    def start(self, symbols: list[str] | None = None) -> AutopilotState:
        if symbols:
            self.state.symbols = [symbol.upper() for symbol in symbols]
        self.state.enabled = True
        self.state.last_action = "Autopilot started in paper mode."
        return self.state

    def stop(self) -> AutopilotState:
        self.state.enabled = False
        self.state.last_action = "Autopilot stopped."
        return self.state

    def run_once(self) -> AutopilotState:
        self.state.last_run_at = datetime.now(UTC)
        self.state.orders = []

        if not self.state.enabled:
            self.state.last_action = "Autopilot is off."
            return self.state

        positions_by_symbol = {
            position.symbol: position for position in self.broker.get_positions()
        }

        for symbol in self.state.symbols:
            candles = self.market_data.candles_for(symbol)
            if not candles:
                continue

            signal = self.strategy.generate_signal(candles)
            position = positions_by_symbol.get(symbol)

            if position is not None:
                if not self.state.auto_sell_enabled:
                    continue

                current_price = self.broker.get_price(symbol)
                sell_decision = self.sell_decision_engine.evaluate(
                    position=position,
                    current_price=current_price,
                    strategy_signal=signal,
                )
                if sell_decision.action == "SELL":
                    result = self.trading_engine.execute(
                        symbol=symbol,
                        signal="SELL",
                        stop_loss=current_price,
                        requested_quantity=sell_decision.quantity,
                    )
                    if result.order is not None:
                        self.state.orders.append(result.order)
                continue

            if signal == "BUY":
                price = self.broker.get_price(symbol)
                result = self.trading_engine.execute(
                    symbol=symbol,
                    signal="BUY",
                    stop_loss=price * 0.95,
                )
                if result.order is not None:
                    self.state.orders.append(result.order)

        if self.state.orders:
            filled = len([order for order in self.state.orders if order.status == "filled"])
            self.state.last_action = f"Autopilot placed {filled} filled paper order(s)."
        else:
            self.state.last_action = "Autopilot checked markets. No trade placed."

        return self.state
