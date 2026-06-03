from trading_bot.broker.paper_broker import PaperBroker
from trading_bot.execution.order_manager import ExecutionRequest, OrderManager


def test_order_manager_executes_buy_signal() -> None:
    broker = PaperBroker(cash=1000, prices={"AAPL": 100})
    manager = OrderManager(broker)

    result = manager.execute_signal(ExecutionRequest("AAPL", "BUY", 1))

    assert result is not None
    assert result.status == "filled"
    assert broker.get_balance() == 900


def test_order_manager_blocks_duplicate_signal() -> None:
    broker = PaperBroker(cash=1000, prices={"AAPL": 100})
    manager = OrderManager(broker)

    manager.execute_signal(ExecutionRequest("AAPL", "BUY", 1))
    result = manager.execute_signal(ExecutionRequest("AAPL", "BUY", 1))

    assert result is not None
    assert result.status == "rejected"
    assert "Duplicate" in result.message


def test_order_manager_ignores_hold_signal() -> None:
    broker = PaperBroker(cash=1000, prices={"AAPL": 100})
    manager = OrderManager(broker)

    assert manager.execute_signal(ExecutionRequest("AAPL", "HOLD", 1)) is None

