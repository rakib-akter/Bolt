from trading_bot.app import BacktestRequest, CandleRequest, add_candle, backtest


def test_backtest_route_returns_pnl_percent() -> None:
    symbol = "BTST"
    closes = [10, 11, 12, 13, 14, 15]
    for close in closes:
        add_candle(
            CandleRequest(
                symbol=symbol,
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1000,
            )
        )

    result = backtest(
        BacktestRequest(
            symbol=symbol,
            starting_cash=1000,
            quantity=1,
            short_window=2,
            long_window=3,
        )
    )

    assert result["pnl_percent"] > 0
    assert result["trade_count"] == len(result["trades"])
    assert result["is_profitable"] is True
