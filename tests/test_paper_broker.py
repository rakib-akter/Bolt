from trading_bot.broker.paper_broker import PaperBroker


def test_paper_broker_fills_buy_and_updates_cash_and_position() -> None:
    broker = PaperBroker(cash=1000, prices={"AAPL": 100})

    result = broker.place_order("AAPL", "buy", 2)

    assert result.status == "filled"
    assert broker.get_balance() == 800
    assert broker.get_positions()[0].quantity == 2


def test_paper_broker_rejects_sell_without_position() -> None:
    broker = PaperBroker(cash=1000, prices={"AAPL": 100})

    result = broker.place_order("AAPL", "sell", 1)

    assert result.status == "rejected"
    assert "Insufficient" in result.message

