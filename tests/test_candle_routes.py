from trading_bot.app import CandleRequest, add_candle, candles


def test_candle_history_route_returns_stored_symbol_candles() -> None:
    payload = CandleRequest(
        symbol="MSFT",
        open=100,
        high=102,
        low=99,
        close=101,
        volume=1200,
    )

    response = add_candle(payload)
    history = candles("MSFT")

    assert response["status"] == "stored"
    assert history[-1]["symbol"] == "MSFT"
    assert history[-1]["close"] == 101
