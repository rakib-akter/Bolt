# Tradebot Backend

Python backend for a modular trading bot. The first target is paper trading with clear separation between broker access, market data, strategy logic, risk checks, order execution, portfolio tracking, and persistence.

## Build Blocks

1. Broker connection
2. Market data and indicators
3. Strategy engine
4. Risk manager
5. Order manager
6. Portfolio manager
7. API and persistence

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the API:

```powershell
uvicorn trading_bot.app:app --reload
```

Run tests:

```powershell
python -m pytest
```

## Safety

This project is designed to start with paper trading. Do not connect real-money broker credentials until broker integrations, risk limits, order handling, and monitoring have been tested.

