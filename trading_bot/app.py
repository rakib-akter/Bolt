from dataclasses import asdict
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from trading_bot.backtesting.engine import BacktestEngine
from trading_bot.broker.alpaca_broker import AlpacaBroker
from trading_bot.broker.base_broker import BaseBroker
from trading_bot.broker.paper_broker import PaperBroker
from trading_bot.config import load_settings
from trading_bot.data.market_data import Candle, MarketDataStore
from trading_bot.database.db import TradeRepository
from trading_bot.execution.autopilot import PaperAutopilot
from trading_bot.execution.paper_trading import PaperTradingEngine
from trading_bot.portfolio.portfolio_manager import PortfolioManager
from trading_bot.risk.risk_manager import RiskManager
from trading_bot.strategy.moving_average_strategy import MovingAverageStrategy
from trading_bot.strategy.registry import STRATEGIES, create_strategy
from trading_bot.strategy.sell_decision import SellDecisionEngine
from trading_bot.utils.logger import get_logger

settings = load_settings()
logger = get_logger(__name__)


def create_broker() -> BaseBroker:
    if settings.broker_name.lower() == "alpaca":
        return AlpacaBroker(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            base_url=settings.alpaca_base_url,
        )
    return PaperBroker(
        cash=settings.default_cash,
        prices={settings.default_symbol: 100.0},
    )


broker = create_broker()
market_data = MarketDataStore()
strategy = MovingAverageStrategy()
sell_decision_engine = SellDecisionEngine()
risk_manager = RiskManager(
    max_risk_per_trade=settings.max_risk_per_trade,
    max_position_value=settings.max_position_value,
)
paper_trading_engine = PaperTradingEngine(broker, risk_manager)
autopilot = PaperAutopilot(
    broker=broker,
    market_data=market_data,
    strategy=strategy,
    trading_engine=paper_trading_engine,
    sell_decision_engine=sell_decision_engine,
)
portfolio_manager = PortfolioManager(broker)
trade_repository = TradeRepository(settings.database_path)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class AutopilotRequest(BaseModel):
    symbols: list[str] | None = None


class AutopilotConfigRequest(BaseModel):
    auto_sell_enabled: bool | None = None
    stop_loss_percent: float | None = None
    take_profit_percent: float | None = None


class BacktestRequest(BaseModel):
    symbol: str
    starting_cash: float = 10000.0
    quantity: float = 1.0
    short_window: int = 5
    long_window: int = 20
    strategy_id: str = "moving_average"


class StrategySelectionRequest(BaseModel):
    strategy_id: str


def backtest_strategy_on_candles(strategy_id: str, symbol: str) -> dict[str, object] | None:
    candles_for_symbol = market_data.candles_for(symbol)
    if not candles_for_symbol:
        return None

    engine = BacktestEngine(
        strategy=create_strategy(strategy_id),
        starting_cash=10000,
    )
    result = engine.run(candles_for_symbol, quantity=1)
    return {
        "symbol": symbol.upper(),
        "pnl_percent": result.pnl_percent,
        "win_rate": result.win_rate,
        "trade_count": result.trade_count,
        "is_profitable": result.is_profitable,
    }


def current_strategy():
    return autopilot.strategy


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.get("/status")
def status() -> dict[str, object]:
    return {
        "environment": settings.environment,
        "broker": settings.broker_name,
        "cash": broker.get_balance(),
        "position_count": len(broker.get_positions()),
        "autopilot_enabled": autopilot.state.enabled,
        "strategy_id": autopilot.state.strategy_id,
    }


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
    logger.info("Stored candle for %s at close %.2f", request.symbol.upper(), request.close)
    return {"symbol": request.symbol.upper(), "status": "stored"}


@app.get("/candles/{symbol}")
def candles(symbol: str) -> list[dict[str, object]]:
    return [asdict(candle) for candle in market_data.candles_for(symbol)]


@app.get("/portfolio")
def portfolio() -> dict[str, object]:
    return asdict(portfolio_manager.snapshot())


@app.get("/trades")
def trades() -> list[dict[str, object]]:
    return [asdict(trade) for trade in trade_repository.list_trades()]


@app.get("/sell-decisions")
def sell_decisions() -> list[dict[str, object]]:
    decisions = []
    for position in broker.get_positions():
        symbol = position.symbol
        candles_for_symbol = market_data.candles_for(symbol)
        signal = current_strategy().generate_signal(candles_for_symbol)
        current_price = broker.get_price(symbol)
        decision = sell_decision_engine.evaluate(position, current_price, signal)
        decisions.append(asdict(decision))
    return decisions


@app.get("/autopilot")
def autopilot_status() -> dict[str, object]:
    return asdict(autopilot.state)


@app.get("/strategies")
def strategies() -> list[dict[str, object]]:
    catalog = []
    for definition in STRATEGIES.values():
        backtests = [
            result
            for symbol in autopilot.state.symbols
            if (result := backtest_strategy_on_candles(definition.id, symbol)) is not None
        ]
        tested = len(backtests)
        average_win_rate = (
            sum(float(result["win_rate"]) for result in backtests) / tested
            if tested
            else None
        )
        average_pnl_percent = (
            sum(float(result["pnl_percent"]) for result in backtests) / tested
            if tested
            else None
        )
        catalog.append(
            {
                "id": definition.id,
                "name": definition.name,
                "description": definition.description,
                "pros": definition.pros,
                "cons": definition.cons,
                "selected": definition.id == autopilot.state.strategy_id,
                "tested_symbols": tested,
                "success_rate": average_win_rate,
                "average_pnl_percent": average_pnl_percent,
            }
        )
    return catalog


@app.post("/strategies/select")
def select_strategy(request: StrategySelectionRequest) -> dict[str, object]:
    try:
        selected = create_strategy(request.strategy_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(autopilot.configure_strategy(request.strategy_id, selected))


@app.post("/backtest")
def backtest(request: BacktestRequest) -> dict[str, object]:
    if request.starting_cash <= 0:
        raise HTTPException(status_code=400, detail="Starting cash must be greater than zero.")
    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")

    candles_for_symbol = market_data.candles_for(request.symbol)
    if not candles_for_symbol:
        raise HTTPException(
            status_code=404,
            detail=f"No candles available for {request.symbol.upper()}.",
        )

    try:
        if request.strategy_id == "moving_average":
            backtest_strategy = MovingAverageStrategy(
                short_window=request.short_window,
                long_window=request.long_window,
            )
        else:
            backtest_strategy = create_strategy(request.strategy_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    engine = BacktestEngine(
        strategy=backtest_strategy,
        starting_cash=request.starting_cash,
    )
    return asdict(engine.run(candles_for_symbol, quantity=request.quantity))


@app.post("/autopilot/start")
def start_autopilot(request: AutopilotRequest) -> dict[str, object]:
    return asdict(autopilot.start(request.symbols))


@app.post("/autopilot/stop")
def stop_autopilot() -> dict[str, object]:
    return asdict(autopilot.stop())


@app.post("/autopilot/config")
def configure_autopilot(request: AutopilotConfigRequest) -> dict[str, object]:
    try:
        state = autopilot.configure_auto_sell(
            auto_sell_enabled=request.auto_sell_enabled,
            stop_loss_percent=request.stop_loss_percent,
            take_profit_percent=request.take_profit_percent,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(state)


@app.post("/autopilot/tick")
def autopilot_tick() -> dict[str, object]:
    state = autopilot.run_once()
    for order in state.orders:
        trade_repository.save_order_result(order)
    return asdict(state)


@app.post("/run-once")
def run_once(request: RunRequest) -> dict[str, object]:
    symbol = request.symbol.upper()
    candles = market_data.candles_for(symbol)
    signal = current_strategy().generate_signal(candles)
    try:
        result = paper_trading_engine.execute(
            symbol=symbol,
            signal=signal,
            stop_loss=request.stop_loss,
            requested_quantity=request.requested_quantity,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    logger.info("Run once completed for %s with signal %s", symbol, result.signal)
    if result.order is not None:
        trade_repository.save_order_result(result.order)
    return {
        "symbol": symbol,
        "signal": result.signal,
        "risk": asdict(result.risk) if result.risk is not None else None,
        "order": asdict(result.order) if result.order is not None else None,
    }
