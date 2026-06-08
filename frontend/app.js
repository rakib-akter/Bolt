const API_BASE = "http://127.0.0.1:8000";

const fields = {
  environment: document.querySelector("#environment"),
  broker: document.querySelector("#broker"),
  cash: document.querySelector("#cash"),
  equity: document.querySelector("#equity"),
  positions: document.querySelector("#positions"),
  marketValue: document.querySelector("#marketValue"),
  unrealized: document.querySelector("#unrealized"),
  tradeCount: document.querySelector("#tradeCount"),
  activityLog: document.querySelector("#activityLog"),
  connectionBadge: document.querySelector("#connectionBadge"),
  sidebarMode: document.querySelector("#sidebarMode"),
  positionSummary: document.querySelector("#positionSummary"),
  lastUpdated: document.querySelector("#lastUpdated"),
  lastAction: document.querySelector("#lastAction"),
  positionsTable: document.querySelector("#positionsTable"),
  tradesTable: document.querySelector("#tradesTable"),
};

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

function money(value) {
  return currency.format(Number(value || 0));
}

function showActivity(label, value) {
  fields.lastAction.textContent = label;
  fields.activityLog.textContent = JSON.stringify(value, null, 2);
}

function setConnection(state, message) {
  fields.connectionBadge.className = `status-pill ${state}`;
  fields.connectionBadge.textContent = message;
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Backend request failed.");
  }
  return data;
}

function renderPositions(positions) {
  if (!positions.length) {
    fields.positionsTable.innerHTML = '<tr><td colspan="6">No open positions.</td></tr>';
    fields.positionSummary.textContent = "No exposure";
    return;
  }

  fields.positionSummary.textContent = `${positions.length} open`;
  fields.positionsTable.innerHTML = positions
    .map((position) => {
      const plClass = position.unrealized_pl >= 0 ? "positive" : "negative";
      return `
        <tr>
          <td>${position.symbol}</td>
          <td>${Number(position.quantity).toFixed(2)}</td>
          <td>${money(position.average_price)}</td>
          <td>${money(position.market_price)}</td>
          <td>${money(position.market_value)}</td>
          <td class="${plClass}">${money(position.unrealized_pl)}</td>
        </tr>
      `;
    })
    .join("");
}

function renderTrades(trades) {
  if (!trades.length) {
    fields.tradesTable.innerHTML = '<tr><td colspan="6">No trades recorded yet.</td></tr>';
    return;
  }

  fields.tradesTable.innerHTML = trades
    .slice(-8)
    .reverse()
    .map(
      (trade) => `
        <tr>
          <td>${trade.id}</td>
          <td>${trade.symbol}</td>
          <td>${trade.side}</td>
          <td>${Number(trade.quantity).toFixed(2)}</td>
          <td>${money(trade.price)}</td>
          <td>${trade.status}</td>
        </tr>
      `,
    )
    .join("");
}

async function refreshDashboard() {
  const [status, portfolio, trades] = await Promise.all([
    request("/status"),
    request("/portfolio"),
    request("/trades"),
  ]);

  fields.environment.textContent = `Environment: ${status.environment}`;
  fields.broker.textContent = `Broker: ${status.broker}`;
  fields.sidebarMode.textContent = status.environment;
  fields.cash.textContent = money(portfolio.cash);
  fields.equity.textContent = money(portfolio.total_equity);
  fields.positions.textContent = status.position_count;
  fields.marketValue.textContent = `Market value: ${money(portfolio.total_market_value)}`;
  fields.unrealized.textContent = money(portfolio.total_unrealized_pl);
  fields.unrealized.className = portfolio.total_unrealized_pl >= 0 ? "positive" : "negative";
  fields.tradeCount.textContent = `Trades: ${trades.length}`;
  fields.lastUpdated.textContent = new Date().toLocaleTimeString();

  renderPositions(portfolio.positions);
  renderTrades(trades);
  setConnection("ok", "Connected");
  showActivity("Dashboard refreshed", { status, portfolio, trades });
}

document.querySelector("#refreshButton").addEventListener("click", () => {
  refreshDashboard().catch((error) => {
    setConnection("error", "Offline");
    showActivity("Refresh failed", { error: error.message });
  });
});

document.querySelector("#candleForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = {
    symbol: form.get("symbol"),
    open: Number(form.get("open")),
    high: Number(form.get("high")),
    low: Number(form.get("low")),
    close: Number(form.get("close")),
    volume: Number(form.get("volume")),
  };
  try {
    const result = await request("/candles", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showActivity("Candle stored", result);
    await refreshDashboard();
  } catch (error) {
    setConnection("error", "Offline");
    showActivity("Candle failed", { error: error.message });
  }
});

document.querySelector("#runForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const quantity = Number(form.get("quantity"));
  const payload = {
    symbol: form.get("symbol"),
    stop_loss: Number(form.get("stopLoss")),
  };
  if (quantity > 0) {
    payload.requested_quantity = quantity;
  }

  try {
    const result = await request("/run-once", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showActivity("Strategy run", result);
    await refreshDashboard();
  } catch (error) {
    setConnection("error", "Offline");
    showActivity("Strategy failed", { error: error.message });
  }
});

refreshDashboard().catch((error) => {
  setConnection("error", "Offline");
  showActivity("Backend unavailable", {
    error: error.message,
    hint: "Start the API with: python -m uvicorn trading_bot.app:app --reload",
  });
});
