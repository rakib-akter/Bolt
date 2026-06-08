from trading_bot.broker.base_broker import Position
from trading_bot.strategy.sell_decision import SellDecisionEngine


def test_sell_decision_sells_when_stop_loss_is_reached() -> None:
    engine = SellDecisionEngine(stop_loss_percent=0.05)
    position = Position("AAPL", quantity=3, average_price=100)

    decision = engine.evaluate(position, current_price=94, strategy_signal="HOLD")

    assert decision.action == "SELL"
    assert decision.quantity == 3
    assert "Stop loss" in decision.reason


def test_sell_decision_sells_when_take_profit_is_reached() -> None:
    engine = SellDecisionEngine(take_profit_percent=0.10)
    position = Position("AAPL", quantity=2, average_price=100)

    decision = engine.evaluate(position, current_price=112, strategy_signal="HOLD")

    assert decision.action == "SELL"
    assert decision.quantity == 2
    assert "Take profit" in decision.reason


def test_sell_decision_holds_when_no_rule_triggers() -> None:
    engine = SellDecisionEngine()
    position = Position("AAPL", quantity=2, average_price=100)

    decision = engine.evaluate(position, current_price=103, strategy_signal="HOLD")

    assert decision.action == "HOLD"

