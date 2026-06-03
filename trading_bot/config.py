from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "Tradebot Backend"
    environment: str = "paper"
    default_symbol: str = "AAPL"
    default_cash: float = 10000.0
    max_risk_per_trade: float = 0.01
    max_position_value: float = 2500.0


def load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", Settings.app_name),
        environment=os.getenv("TRADING_ENV", Settings.environment),
        default_symbol=os.getenv("DEFAULT_SYMBOL", Settings.default_symbol),
        default_cash=float(os.getenv("DEFAULT_CASH", Settings.default_cash)),
        max_risk_per_trade=float(
            os.getenv("MAX_RISK_PER_TRADE", Settings.max_risk_per_trade)
        ),
        max_position_value=float(
            os.getenv("MAX_POSITION_VALUE", Settings.max_position_value)
        ),
    )

