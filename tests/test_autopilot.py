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


def test_autopilot_sells_paper_position_when_stop_loss_triggers() -> None:
    broker = PaperBroker(cash=1000, prices={"AAPL": 120})
    broker.place_order("AAPL", "buy", 2)
    broker.set_price("AAPL", 108)
    store = make_candles("AAPL", [130, 128, 126, 124, 120, 112, 108])
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

    assert state.orders
    assert state.orders[0].side == "sell"
    assert broker.get_positions() == []


def test_autopilot_keeps_position_when_auto_sell_is_off() -> None:
    broker = PaperBroker(cash=1000, prices={"AAPL": 120})
    broker.place_order("AAPL", "buy", 2)
    broker.set_price("AAPL", 108)
    store = make_candles("AAPL", [130, 128, 126, 124, 120, 112, 108])
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
    autopilot.configure_auto_sell(auto_sell_enabled=False)
    state = autopilot.run_once()

    assert state.orders == []
    assert broker.get_positions()[0].symbol == "AAPL"


def test_autopilot_limits_new_buys_to_max_active_symbols() -> None:
    broker = PaperBroker(cash=5000, prices={"AAPL": 120, "MSFT": 120})
    store = make_candles("AAPL", [100, 101, 102, 103, 110, 115, 120])
    for candle in make_candles("MSFT", [100, 101, 102, 103, 110, 115, 120]).candles_for("MSFT"):
        store.add_candle(candle)
    strategy = MovingAverageStrategy(short_window=2, long_window=5)
    trading_engine = PaperTradingEngine(broker, RiskManager(max_position_value=500))
    autopilot = PaperAutopilot(
        broker=broker,
        market_data=store,
        strategy=strategy,
        trading_engine=trading_engine,
        sell_decision_engine=SellDecisionEngine(),
    )

    autopilot.configure_symbols(["AAPL", "MSFT"], max_active_symbols=1)
    autopilot.start()
    state = autopilot.run_once()

    assert len([order for order in state.orders if order.status == "filled"]) == 1
    assert len(broker.get_positions()) == 1
