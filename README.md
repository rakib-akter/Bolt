# Tradebot Backend

Python backend for a modular trading bot. The first target is paper trading with clear separation between broker access, market data, strategy logic, risk checks, order execution, portfolio tracking, and persistence.

## Build Blocks

1. Broker connection
2. Market data and indicators
3. Strategy engine
4. Risk manager
5. Order manager
6. Portfolio manager
7. Backtesting skeleton
8. API and persistence
9. Static dashboard

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the API:

```powershell
python -m uvicorn trading_bot.app:app --reload
```

Run tests:

```powershell
python -m pytest
```

## Configuration

The backend starts in paper mode by default. Environment variables can override the defaults:

```powershell
$env:BROKER_NAME="paper"
$env:DEFAULT_SYMBOL="AAPL"
$env:DEFAULT_CASH="10000"
$env:MAX_RISK_PER_TRADE="0.01"
$env:MAX_POSITION_VALUE="2500"
$env:DATABASE_PATH="tradebot.sqlite3"
```

For Alpaca paper trading:

```powershell
$env:BROKER_NAME="alpaca"
$env:ALPACA_API_KEY="your-key"
$env:ALPACA_SECRET_KEY="your-secret"
$env:ALPACA_BASE_URL="https://paper-api.alpaca.markets"
```

## API Routes

- `GET /health`
- `GET /status`
- `GET /portfolio`
- `GET /trades`
- `POST /prices`
- `POST /candles`
- `POST /run-once`

## Dashboard

Start the backend, then open [frontend/index.html](frontend/index.html). The dashboard shows backend status, cash, positions, latest activity, and simple controls for adding candles and running the strategy once.

## Safety

This project is designed to start with paper trading. Do not connect real-money broker credentials until broker integrations, risk limits, order handling, and monitoring have been tested.
