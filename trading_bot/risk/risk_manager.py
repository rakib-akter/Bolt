from dataclasses import dataclass


@dataclass(frozen=True)
class TradeRiskDecision:
    approved: bool
    quantity: float
    reason: str


@dataclass(frozen=True)
class RiskManager:
    max_risk_per_trade: float = 0.01
    max_position_value: float = 2500.0

    def __post_init__(self) -> None:
        if not 0 < self.max_risk_per_trade <= 1:
            raise ValueError("Max risk per trade must be between 0 and 1.")
        if self.max_position_value <= 0:
            raise ValueError("Max position value must be greater than zero.")

    def approve_trade(
        self,
        balance: float,
        price: float,
        stop_loss: float,
        requested_quantity: float | None = None,
    ) -> TradeRiskDecision:
        if balance <= 0:
            return TradeRiskDecision(False, 0, "Balance must be greater than zero.")
        if price <= 0:
            return TradeRiskDecision(False, 0, "Price must be greater than zero.")
        if stop_loss <= 0:
            return TradeRiskDecision(False, 0, "Stop loss must be greater than zero.")

        risk_per_unit = abs(price - stop_loss)
        if risk_per_unit == 0:
            return TradeRiskDecision(False, 0, "Stop loss cannot equal entry price.")

        max_risk_amount = balance * self.max_risk_per_trade
        risk_based_quantity = max_risk_amount / risk_per_unit
        value_based_quantity = self.max_position_value / price
        approved_quantity = min(risk_based_quantity, value_based_quantity)

        if requested_quantity is not None:
            if requested_quantity <= 0:
                return TradeRiskDecision(False, 0, "Requested quantity must be positive.")
            approved_quantity = min(approved_quantity, requested_quantity)

        if approved_quantity <= 0:
            return TradeRiskDecision(False, 0, "Approved quantity is zero.")

        return TradeRiskDecision(True, approved_quantity, "Approved.")

