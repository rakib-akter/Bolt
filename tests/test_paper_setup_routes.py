from trading_bot.app import PaperSetupRequest, autopilot, candles, portfolio, setup_paper_trading


def test_paper_setup_seeds_candles_and_starts_autopilot() -> None:
    response = setup_paper_trading(
        PaperSetupRequest(
            symbols=["AAPL", "MSFT"],
            starting_cash=25000,
            candles_per_symbol=35,
        )
    )

    assert response["mode"] == "paper"
    assert response["cash"] == 25000
    assert response["autopilot"]["enabled"] is True
    assert autopilot.state.symbols == ["AAPL", "MSFT"]
    assert len(candles("AAPL")) == 35
    assert portfolio()["cash"] == 25000
