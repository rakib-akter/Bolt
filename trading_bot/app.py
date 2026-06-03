from dataclasses import asdict
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from trading_bot.broker.paper_broker import PaperBroker
from trading_bot.config import load_settings
from trading_bot.data.market_data import Candle, MarketDataStore
from trading_bot.database.db import TradeRepository
from trading_bot.execution.order_manager import ExecutionRequest, OrderManager
from trading_bot.portfolio.portfolio_manager import PortfolioManager
from trading_bot.risk.risk_manager import RiskManager
from trading_bot.strategy.moving_average_strategy import MovingAverageStrategy

settings = load_settings()
broker = PaperBroker(cash=settings.default_cash, prices={settings.default_symbol: 100.0})
market_data = MarketDataStore()
strategy = MovingAverageStrategy()
risk_manager = RiskManager(
    max_risk_per_trade=settings.max_risk_per_trade,
    max_position_value=settings.max_position_value,
)
order_manager = OrderManager(broker)
portfolio_manager = PortfolioManager(broker)
trade_repository = TradeRepository()

app = FastAPI(title=settings.app_name)


class PriceRequest(BaseModel):
    symbol: str
    price: float


class CandleRequest(BaseModel):
    symbol: str
    timestamp: datetime | None = None
    open: float
    high: float
    low: float
    close: float
    volume: float


class RunRequest(BaseModel):
    symbol: str
    stop_loss: float
    requested_quantity: float | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.post("/prices")
def set_price(request: PriceRequest) -> dict[str, float | str]:
    try:
        broker.set_price(request.symbol, request.price)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"symbol": request.symbol.upper(), "price": request.price}


@app.post("/candles")
def add_candle(request: CandleRequest) -> dict[str, str]:
    timestamp = request.timestamp or datetime.now(UTC)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    try:
        candle = Candle(
            symbol=request.symbol.upper(),
            timestamp=timestamp,
            open=request.open,
            high=request.high,
            low=request.low,
            close=request.close,
            volume=request.volume,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    market_data.add_candle(candle)
    broker.set_price(request.symbol, request.close)
    return {"symbol": request.symbol.upper(), "status": "stored"}


@app.get("/portfolio")
def portfolio() -> dict[str, object]:
    return asdict(portfolio_manager.snapshot())


@app.get("/trades")
def trades() -> list[dict[str, object]]:
    return [asdict(trade) for trade in trade_repository.list_trades()]


@app.post("/run-once")
def run_once(request: RunRequest) -> dict[str, object]:
    symbol = request.symbol.upper()
    candles = market_data.candles_for(symbol)
    signal = strategy.generate_signal(candles)
    if signal == "HOLD":
        return {"symbol": symbol, "signal": signal, "order": None, "risk": None}

    price = broker.get_price(symbol)
    decision = risk_manager.approve_trade(
        balance=broker.get_balance(),
        price=price,
        stop_loss=request.stop_loss,
        requested_quantity=request.requested_quantity,
    )
    if not decision.approved:
        return {
            "symbol": symbol,
            "signal": signal,
            "order": None,
            "risk": asdict(decision),
        }

    result = order_manager.execute_signal(
        ExecutionRequest(symbol=symbol, signal=signal, quantity=decision.quantity)
    )
    if result is not None:
        trade_repository.save_order_result(result)
    return {
        "symbol": symbol,
        "signal": signal,
        "risk": asdict(decision),
        "order": asdict(result) if result is not None else None,
    }
