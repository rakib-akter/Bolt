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
  sellSignalsTable: document.querySelector("#sellSignalsTable"),
  sellSummary: document.querySelector("#sellSummary"),
  priceChart: document.querySelector("#priceChart"),
  chartEmpty: document.querySelector("#chartEmpty"),
  chartSummary: document.querySelector("#chartSummary"),
  chartLast: document.querySelector("#chartLast"),
  chartHigh: document.querySelector("#chartHigh"),
  chartLow: document.querySelector("#chartLow"),
  chartVolume: document.querySelector("#chartVolume"),
  chartTitle: document.querySelector("#chartTitle"),
  liveRefreshToggle: document.querySelector("#liveRefreshToggle"),
  liveMarketToggle: document.querySelector("#liveMarketToggle"),
  watchlist: document.querySelector("#watchlist"),
  watchlistStatus: document.querySelector("#watchlistStatus"),
  cashSparkline: document.querySelector("#cashSparkline"),
  equitySparkline: document.querySelector("#equitySparkline"),
  positionsSparkline: document.querySelector("#positionsSparkline"),
  plSparkline: document.querySelector("#plSparkline"),
};

let activeChartSymbol = "AAPL";
let liveRefreshTimer;
let liveMarketTimer;
let activeChartRange = "all";
let latestCandles = [];
const watchlistSymbols = ["AAPL", "MSFT", "NVDA", "TSLA", "SPY"];
const metricHistory = {
  cash: [],
  equity: [],
  positions: [],
  pl: [],
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

function renderSellDecisions(decisions) {
  if (!decisions.length) {
    fields.sellSignalsTable.innerHTML = '<tr><td colspan="6">No open positions to evaluate.</td></tr>';
    fields.sellSummary.textContent = "No recommendations";
    return;
  }

  const sellCount = decisions.filter((decision) => decision.action === "SELL").length;
  fields.sellSummary.textContent = sellCount ? `${sellCount} sell signal(s)` : "All holds";
  fields.sellSignalsTable.innerHTML = decisions
    .map((decision) => {
      const actionClass = decision.action === "SELL" ? "negative" : "positive";
      const plClass = decision.unrealized_pl_percent >= 0 ? "positive" : "negative";
      return `
        <tr>
          <td>${decision.symbol}</td>
          <td class="${actionClass}">${decision.action}</td>
          <td>${Number(decision.quantity).toFixed(2)}</td>
          <td>${money(decision.current_price)}</td>
          <td class="${plClass}">${(Number(decision.unrealized_pl_percent) * 100).toFixed(2)}%</td>
          <td>${decision.reason}</td>
        </tr>
      `;
    })
    .join("");
}

function changePercent(candles) {
  if (candles.length < 2) {
    return 0;
  }
  const first = Number(candles[0].close);
  const last = Number(candles.at(-1).close);
  return first ? (last - first) / first : 0;
}

function visibleCandles(candles) {
  if (activeChartRange === "all") {
    return candles;
  }
  return candles.slice(-Number(activeChartRange));
}

async function renderWatchlist() {
  const rows = await Promise.all(
    watchlistSymbols.map(async (symbol) => {
      const candles = await request(`/candles/${symbol}`);
      const lastClose = candles.length ? Number(candles.at(-1).close) : 0;
      const change = changePercent(candles);
      return { symbol, candles, lastClose, change };
    }),
  );

  fields.watchlistStatus.textContent = `${rows.length} symbols`;
  fields.watchlist.innerHTML = rows
    .map((row) => {
      const changeClass = row.change >= 0 ? "positive" : "negative";
      const activeClass = row.symbol === activeChartSymbol ? " active" : "";
      return `
        <button class="watchlist-item${activeClass}" type="button" data-symbol="${row.symbol}">
          <span class="watchlist-row">
            <span class="watchlist-symbol">${row.symbol}</span>
            <span class="watchlist-price">${row.lastClose ? money(row.lastClose) : "-"}</span>
          </span>
          <span class="watchlist-row">
            <span class="watchlist-meta">${row.candles.length} candles</span>
            <span class="${changeClass}">${(row.change * 100).toFixed(2)}%</span>
          </span>
        </button>
      `;
    })
    .join("");
}

function resizeCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * ratio));
  canvas.height = Math.max(1, Math.floor(rect.height * ratio));
  return ratio;
}

function movingAverage(values, windowSize) {
  return values.map((_, index) => {
    const start = Math.max(0, index - windowSize + 1);
    const window = values.slice(start, index + 1);
    return window.reduce((total, value) => total + value, 0) / window.length;
  });
}

function chartPoint(value, index, values, width, height, padding) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const xStep = values.length > 1 ? (width - padding * 2) / (values.length - 1) : 0;
  return {
    x: padding + xStep * index,
    y: height - padding - ((value - min) / range) * (height - padding * 2),
  };
}

function drawPriceChart(candles, symbol) {
  latestCandles = candles;
  const canvas = fields.priceChart;
  resizeCanvas(canvas);
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);

  const displayCandles = visibleCandles(candles);

  if (!displayCandles.length) {
    fields.chartEmpty.classList.add("visible");
    fields.chartSummary.textContent = `${symbol}: no candles`;
    fields.chartTitle.textContent = symbol;
    fields.chartLast.textContent = "-";
    fields.chartHigh.textContent = "-";
    fields.chartLow.textContent = "-";
    fields.chartVolume.textContent = "-";
    return;
  }

  fields.chartEmpty.classList.remove("visible");
  const padding = 42;
  const closes = displayCandles.map((candle) => Number(candle.close));
  const volumes = displayCandles.map((candle) => Number(candle.volume || 0));
  const minPrice = Math.min(...closes);
  const maxPrice = Math.max(...closes);
  const maValues = movingAverage(closes, 5);
  const maxVolume = Math.max(...volumes, 1);

  context.strokeStyle = "#1d3556";
  context.lineWidth = 1;
  context.beginPath();
  for (let index = 0; index < 4; index += 1) {
    const y = padding + ((height - padding * 2) / 3) * index;
    context.moveTo(padding, y);
    context.lineTo(width - padding, y);
  }
  context.stroke();

  volumes.forEach((volume, index) => {
    const barWidth = Math.max(3, (width - padding * 2) / Math.max(volumes.length, 1) - 4);
    const x = padding + ((width - padding * 2) / Math.max(volumes.length, 1)) * index;
    const barHeight = (volume / maxVolume) * 54;
    context.fillStyle = "rgba(59, 130, 246, 0.28)";
    context.fillRect(x, height - padding - barHeight, barWidth, barHeight);
  });

  const gradient = context.createLinearGradient(0, padding, 0, height - padding);
  gradient.addColorStop(0, "rgba(56, 189, 248, 0.24)");
  gradient.addColorStop(1, "rgba(56, 189, 248, 0.03)");

  context.beginPath();
  closes.forEach((close, index) => {
    const point = chartPoint(close, index, closes, width, height, padding);
    if (index === 0) {
      context.moveTo(point.x, point.y);
    } else {
      context.lineTo(point.x, point.y);
    }
  });
  const lastPoint = chartPoint(closes.at(-1), closes.length - 1, closes, width, height, padding);
  const firstPoint = chartPoint(closes[0], 0, closes, width, height, padding);
  context.lineTo(lastPoint.x, height - padding);
  context.lineTo(firstPoint.x, height - padding);
  context.closePath();
  context.fillStyle = gradient;
  context.fill();

  context.strokeStyle = "#38bdf8";
  context.lineWidth = 3;
  context.beginPath();
  closes.forEach((close, index) => {
    const { x, y } = chartPoint(close, index, closes, width, height, padding);
    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });
  context.stroke();

  context.strokeStyle = "#a78bfa";
  context.lineWidth = 2;
  context.beginPath();
  maValues.forEach((value, index) => {
    const { x, y } = chartPoint(value, index, closes, width, height, padding);
    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });
  context.stroke();

  context.fillStyle = "#38bdf8";
  const markerStart = Math.max(0, closes.length - 8);
  closes.slice(markerStart).forEach((close, offset) => {
    const index = markerStart + offset;
    const { x, y } = chartPoint(close, index, closes, width, height, padding);
    context.beginPath();
    context.arc(x, y, 4.5, 0, Math.PI * 2);
    context.fill();
  });

  context.fillStyle = "#c9d7eb";
  context.font = `${13 * (window.devicePixelRatio || 1)}px Segoe UI, Arial`;
  context.fillText(money(maxPrice), 8, padding + 4);
  context.fillText(money(minPrice), 8, height - padding + 4);
  fields.chartTitle.textContent = symbol;
  fields.chartSummary.textContent = `${displayCandles.length}/${candles.length} candles shown`;
  fields.chartLast.textContent = money(closes.at(-1));
  fields.chartHigh.textContent = money(maxPrice);
  fields.chartLow.textContent = money(minPrice);
  fields.chartVolume.textContent = volumes.at(-1).toLocaleString();
}

async function loadChart(symbol = activeChartSymbol) {
  activeChartSymbol = symbol.toUpperCase();
  const candles = await request(`/candles/${activeChartSymbol}`);
  drawPriceChart(candles, activeChartSymbol);
}

function pushMetric(history, value) {
  history.push(Number(value || 0));
  if (history.length > 28) {
    history.shift();
  }
}

function drawSparkline(canvas, values, color) {
  resizeCanvas(canvas);
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);
  if (values.length < 2) {
    return;
  }
  const padding = 6;
  context.strokeStyle = color;
  context.lineWidth = 2.5 * (window.devicePixelRatio || 1);
  context.beginPath();
  values.forEach((value, index) => {
    const { x, y } = chartPoint(value, index, values, width, height, padding);
    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });
  context.stroke();
}

function renderMetricSparklines(portfolio, status) {
  pushMetric(metricHistory.cash, portfolio.cash);
  pushMetric(metricHistory.equity, portfolio.total_equity);
  pushMetric(metricHistory.positions, status.position_count);
  pushMetric(metricHistory.pl, portfolio.total_unrealized_pl);

  drawSparkline(fields.cashSparkline, metricHistory.cash, "#38bdf8");
  drawSparkline(fields.equitySparkline, metricHistory.equity, "#60a5fa");
  drawSparkline(fields.positionsSparkline, metricHistory.positions, "#93c5fd");
  drawSparkline(
    fields.plSparkline,
    metricHistory.pl,
    portfolio.total_unrealized_pl >= 0 ? "#5eead4" : "#fca5a5",
  );
}

async function addDemoCandles(symbol) {
  let price = 100 + Math.random() * 8;
  for (let index = 0; index < 24; index += 1) {
    const move = Math.sin(index / 2.2) * 1.4 + (Math.random() - 0.45) * 1.8;
    const open = price;
    const close = Math.max(1, open + move);
    const high = Math.max(open, close) + Math.random() * 1.2;
    const low = Math.max(0.01, Math.min(open, close) - Math.random() * 1.2);
    price = close;
    await request("/candles", {
      method: "POST",
      body: JSON.stringify({
        symbol,
        open,
        high,
        low,
        close,
        volume: 1000 + index * 25,
      }),
    });
  }
}

async function addLiveTick(symbol) {
  const candles = await request(`/candles/${symbol}`);
  const previous = candles.length ? Number(candles.at(-1).close) : 100 + Math.random() * 12;
  const move = (Math.random() - 0.48) * 2.1;
  const open = previous;
  const close = Math.max(1, previous + move);
  const high = Math.max(open, close) + Math.random() * 0.75;
  const low = Math.max(0.01, Math.min(open, close) - Math.random() * 0.75);
  await request("/candles", {
    method: "POST",
    body: JSON.stringify({
      symbol,
      open,
      high,
      low,
      close,
      volume: 1200 + Math.round(Math.random() * 1800),
    }),
  });
}

async function refreshDashboard() {
  const [status, portfolio, trades, sellDecisions] = await Promise.all([
    request("/status"),
    request("/portfolio"),
    request("/trades"),
    request("/sell-decisions"),
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
  renderSellDecisions(sellDecisions);
  renderMetricSparklines(portfolio, status);
  await loadChart(activeChartSymbol);
  await renderWatchlist();
  setConnection("ok", "Connected");
  showActivity("Dashboard refreshed", { status, portfolio, trades, sellDecisions });
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
    activeChartSymbol = String(payload.symbol).toUpperCase();
    await refreshDashboard();
  } catch (error) {
    setConnection("error", "Offline");
    showActivity("Candle failed", { error: error.message });
  }
});

document.querySelector("#symbolSearchForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const symbol = String(form.get("symbol")).toUpperCase();
  try {
    await loadChart(symbol);
    await renderWatchlist();
    showActivity("Chart loaded", { symbol });
  } catch (error) {
    setConnection("error", "Offline");
    showActivity("Chart failed", { error: error.message });
  }
});

document.querySelector("#seedCandlesButton").addEventListener("click", async () => {
  const form = new FormData(document.querySelector("#symbolSearchForm"));
  const symbol = String(form.get("symbol")).toUpperCase();
  try {
    await addDemoCandles(symbol);
    await loadChart(symbol);
    await renderWatchlist();
    await refreshDashboard();
    showActivity("Demo candles added", { symbol });
  } catch (error) {
    setConnection("error", "Offline");
    showActivity("Demo candle failed", { error: error.message });
  }
});

document.querySelectorAll(".range-button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".range-button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    activeChartRange = button.dataset.range;
    drawPriceChart(latestCandles, activeChartSymbol);
  });
});

fields.watchlist.addEventListener("click", async (event) => {
  const item = event.target.closest("[data-symbol]");
  if (!item) {
    return;
  }
  const symbol = item.dataset.symbol;
  document.querySelector("#symbolSearchForm input[name='symbol']").value = symbol;
  await loadChart(symbol);
  await renderWatchlist();
  showActivity("Watchlist symbol loaded", { symbol });
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

function startLiveRefresh() {
  clearInterval(liveRefreshTimer);
  if (!fields.liveRefreshToggle.checked) {
    return;
  }
  liveRefreshTimer = setInterval(() => {
    refreshDashboard().catch((error) => {
      setConnection("error", "Offline");
      showActivity("Live refresh failed", { error: error.message });
    });
  }, 5000);
}

fields.liveRefreshToggle.addEventListener("change", () => {
  startLiveRefresh();
  showActivity(fields.liveRefreshToggle.checked ? "Live refresh on" : "Live refresh off", {
    interval_seconds: 5,
  });
});

function startLiveMarket() {
  clearInterval(liveMarketTimer);
  if (!fields.liveMarketToggle.checked) {
    return;
  }
  liveMarketTimer = setInterval(async () => {
    try {
      await addLiveTick(activeChartSymbol);
      await loadChart(activeChartSymbol);
      await renderWatchlist();
      showActivity("Live tick added", { symbol: activeChartSymbol });
    } catch (error) {
      setConnection("error", "Offline");
      showActivity("Live tick failed", { error: error.message });
    }
  }, 2500);
}

fields.liveMarketToggle.addEventListener("change", () => {
  startLiveMarket();
  showActivity(fields.liveMarketToggle.checked ? "Simulated ticks on" : "Simulated ticks off", {
    symbol: activeChartSymbol,
    interval_seconds: 2.5,
  });
});

window.addEventListener("resize", () => {
  loadChart(activeChartSymbol).catch(() => undefined);
  drawSparkline(fields.cashSparkline, metricHistory.cash, "#38bdf8");
  drawSparkline(fields.equitySparkline, metricHistory.equity, "#60a5fa");
  drawSparkline(fields.positionsSparkline, metricHistory.positions, "#93c5fd");
  drawSparkline(fields.plSparkline, metricHistory.pl, "#5eead4");
});

refreshDashboard().catch((error) => {
  setConnection("error", "Offline");
  showActivity("Backend unavailable", {
    error: error.message,
    hint: "Start the API with: python -m uvicorn trading_bot.app:app --reload",
  });
});
startLiveRefresh();
startLiveMarket();
