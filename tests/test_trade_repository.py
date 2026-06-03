from trading_bot.broker.base_broker import OrderResult
from trading_bot.database.db import TradeRepository


def test_trade_repository_saves_order_results(tmp_path) -> None:
    repository = TradeRepository(tmp_path / "trades.sqlite3")

    record = repository.save_order_result(
        OrderResult("AAPL", "buy", 2, 100, "filled", "")
    )

    trades = repository.list_trades()
    assert record.id == 1
    assert trades[0].symbol == "AAPL"
    assert trades[0].status == "filled"

