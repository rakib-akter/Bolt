# Tradebot Dashboard

Static dashboard for watching the paper trading backend.

Start the backend first:

```powershell
python -m uvicorn trading_bot.app:app --reload
```

Then open `frontend/index.html` in a browser.

The dashboard calls `http://127.0.0.1:8000` for status, portfolio, trades, candle creation, and run-once execution.

