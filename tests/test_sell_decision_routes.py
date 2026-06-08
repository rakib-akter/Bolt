from trading_bot.app import broker, sell_decisions


def test_sell_decisions_returns_recommendation_for_open_position() -> None:
    broker.set_price("TSLA", 100)
    broker.place_order("TSLA", "buy", 1)
    broker.set_price("TSLA", 112)

    decisions = sell_decisions()
    tsla_decisions = [item for item in decisions if item["symbol"] == "TSLA"]

    assert tsla_decisions[-1]["action"] == "SELL"
    assert "Take profit" in tsla_decisions[-1]["reason"]
