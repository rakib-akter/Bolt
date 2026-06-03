from trading_bot.risk.risk_manager import RiskManager


def test_risk_manager_sizes_position_from_account_risk() -> None:
    manager = RiskManager(max_risk_per_trade=0.01, max_position_value=10000)

    decision = manager.approve_trade(balance=1000, price=100, stop_loss=95)

    assert decision.approved is True
    assert decision.quantity == 2


def test_risk_manager_caps_position_value() -> None:
    manager = RiskManager(max_risk_per_trade=0.10, max_position_value=250)

    decision = manager.approve_trade(balance=1000, price=100, stop_loss=90)

    assert decision.approved is True
    assert decision.quantity == 2.5


def test_risk_manager_rejects_zero_distance_stop() -> None:
    manager = RiskManager()

    decision = manager.approve_trade(balance=1000, price=100, stop_loss=100)

    assert decision.approved is False

