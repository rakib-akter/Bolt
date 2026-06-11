from datetime import UTC, datetime, timedelta

from trading_bot.broker.paper_broker import PaperBroker
from trading_bot.data.market_data import Candle, MarketDataStore
from trading_bot.execution.autopilot import PaperAutopilot
from trading_bot.execution.paper_trading import PaperTradingEngine
from trading_bot.risk.risk_manager import RiskManager
from trading_bot.strategy.moving_average_strategy import MovingAverageStrategy
from trading_bot.strategy.sell_decision import SellDecisionEngine


def make_candles(symbol: str, closes: list[float]) -> MarketDataStore:
    store = MarketDataStore()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    for index, close in enumerate(closes):
        store.add_candle(
            Candle(
                symbol=symbol,
                timestamp=start + timedelta(days=index),
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1000,
            )
        )
    return store


def test_autopilot_places_paper_buy_when_strategy_is_buy() -> None:
    broker = PaperBroker(cash=1000, prices={"AAPL": 120})
    store = make_candles("AAPL", [100, 101, 102, 103, 110, 115, 120])
    strategy = MovingAverageStrategy(short_window=2, long_window=5)
    trading_engine = PaperTradingEngine(broker, RiskManager(max_position_value=500))
    autopilot = PaperAutopilot(
        broker=broker,
        market_data=store,
        strategy=strategy,
        trading_engine=trading_engine,
        sell_decision_engine=SellDecisionEngine(),
    )

    autopilot.start(["AAPL"])
    state = autopilot.run_once()

    assert state.enabled is True
    assert state.orders
    assert state.orders[0].side == "buy"
    assert broker.get_positions()[0].symbol == "AAPL"

