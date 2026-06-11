from trading_bot.app import (
    CandleRequest,
    StrategySelectionRequest,
    add_candle,
    select_strategy,
    strategies,
)


def test_strategy_catalog_includes_success_rates_from_stored_candles() -> None:
    symbol = "AAPL"
    for index in range(30):
        close = 100 + index
        add_candle(
            CandleRequest(
                symbol=symbol,
                open=close,
                high=close + 1,
                low=close - 1,
                close=close,
                volume=1000,
            )
        )

    select_strategy(StrategySelectionRequest(strategy_id="moving_average"))
    catalog = strategies()
    moving_average = [item for item in catalog if item["id"] == "moving_average"][0]

    assert moving_average["selected"] is True
    assert moving_average["tested_symbols"] >= 1
    assert moving_average["success_rate"] is not None


def test_select_strategy_updates_autopilot_state() -> None:
    state = select_strategy(StrategySelectionRequest(strategy_id="momentum"))

    assert state["strategy_id"] == "momentum"
