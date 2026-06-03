from trading_bot.broker.paper_broker import PaperBroker
from trading_bot.portfolio.portfolio_manager import PortfolioManager


def test_portfolio_snapshot_calculates_equity_and_unrealized_pl() -> None:
    broker = PaperBroker(cash=1000, prices={"AAPL": 100})
    broker.place_order("AAPL", "buy", 2)
    broker.set_price("AAPL", 110)
    manager = PortfolioManager(broker)

    snapshot = manager.snapshot()

    assert snapshot.cash == 800
    assert snapshot.total_market_value == 220
    assert snapshot.total_unrealized_pl == 20
    assert snapshot.total_equity == 1020

