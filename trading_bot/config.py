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
    database_path: str = "tradebot.sqlite3"
    broker_name: str = "paper"
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"


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
        database_path=os.getenv("DATABASE_PATH", Settings.database_path),
        broker_name=os.getenv("BROKER_NAME", Settings.broker_name),
        alpaca_api_key=os.getenv("ALPACA_API_KEY", Settings.alpaca_api_key),
        alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY", Settings.alpaca_secret_key),
        alpaca_base_url=os.getenv("ALPACA_BASE_URL", Settings.alpaca_base_url),
    )
