from trading_bot.app import (
    BacktestCompareRequest,
    PaperSetupRequest,
    TradingUniverseRequest,
    autopilot,
    compare_backtests,
    configure_trading_universe,
    setup_paper_trading,
)


def test_configure_trading_universe_updates_symbol_limit() -> None:
    state = configure_trading_universe(
        TradingUniverseRequest(
            symbols=["AAPL", "MSFT", "NVDA"],
            max_active_symbols=2,
        )
    )

    assert state["symbols"] == ["AAPL", "MSFT", "NVDA"]
    assert state["max_active_symbols"] == 2
    assert autopilot.state.max_active_symbols == 2


def test_compare_backtests_returns_pnl_winner() -> None:
    setup_paper_trading(
        PaperSetupRequest(
            symbols=["AAPL", "MSFT"],
            max_active_symbols=2,
            candles_per_symbol=40,
        )
    )

    result = compare_backtests(
        BacktestCompareRequest(
            first_symbol="AAPL",
            second_symbol="MSFT",
            strategy_id="moving_average",
        )
    )

    assert result["first"]["symbol"] == "AAPL"
    assert result["second"]["symbol"] == "MSFT"
    assert result["winner"] in {"AAPL", "MSFT", "tie"}
    assert result["pnl_gap_percent"] >= 0
