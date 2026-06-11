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
  connectionBadge: document.querySelector("#connectionBadge"),
  notification: document.querySelector("#notification"),
  autopilotStatus: document.querySelector("#autopilotStatus"),
  autopilotMode: document.querySelector("#autopilotMode"),
  autopilotLastAction: document.querySelector("#autopilotLastAction"),
  autoSellSummary: document.querySelector("#autoSellSummary"),
  autoSellToggle: document.querySelector("#autoSellToggle"),
  stopLossPercent: document.querySelector("#stopLossPercent"),
  takeProfitPercent: document.querySelector("#takeProfitPercent"),
  backtestSummary: document.querySelector("#backtestSummary"),
  backtestVerdict: document.querySelector("#backtestVerdict"),
  backtestPnl: document.querySelector("#backtestPnl"),
  backtestEquity: document.querySelector("#backtestEquity"),
  backtestTrades: document.querySelector("#backtestTrades"),
  backtestWinRate: document.querySelector("#backtestWinRate"),
  strategySummary: document.querySelector("#strategySummary"),
  selectedStrategyBadge: document.querySelector("#selectedStrategyBadge"),
  strategyList: document.querySelector("#strategyList"),
  backtestStrategySelect: document.querySelector("#backtestStrategySelect"),
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
let autopilotTimer;
let activeChartRange = "all";
let activeChartTimeframe = "1m";
let latestCandles = [];
const localCandleCache = new Map();
const watchlistSymbols = ["AAPL", "MSFT", "NVDA", "TSLA", "SPY"];
const timeframeConfig = {
  "1m": { label: "1m", ms: 60_000, count: 64 },
  "5m": { label: "5m", ms: 5 * 60_000, count: 64 },
  "15m": { label: "15m", ms: 15 * 60_000, count: 64 },
  "1h": { label: "1h", ms: 60 * 60_000, count: 72 },
  "1d": { label: "1d", ms: 24 * 60 * 60_000, count: 90 },
};
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
  fields.notification.textContent = value?.error ? `${label}: ${value.error}` : label;
  fields.notification.classList.add("visible");
  clearTimeout(showActivity.timeout);
  showActivity.timeout = setTimeout(() => {
    fields.notification.classList.remove("visible");
  }, 2800);
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

function renderAutopilot(state) {
  const enabled = Boolean(state.enabled);
  const autoSellEnabled = Boolean(state.auto_sell_enabled);
  const stopLossPercent = Number(state.stop_loss_percent || 0.05) * 100;
  const takeProfitPercent = Number(state.take_profit_percent || 0.10) * 100;
  fields.autopilotStatus.textContent = enabled ? "Paper autopilot is running" : "Paper autopilot is off";
  fields.autopilotMode.textContent = enabled ? "Auto Paper" : "Manual";
  fields.autopilotMode.className = `status-pill ${enabled ? "ok" : "warning"}`;
  fields.autoSellToggle.checked = autoSellEnabled;
  fields.stopLossPercent.value = stopLossPercent.toFixed(1).replace(".0", "");
  fields.takeProfitPercent.value = takeProfitPercent.toFixed(1).replace(".0", "");
  fields.autoSellSummary.textContent = autoSellEnabled
    ? `Auto exits at -${fields.stopLossPercent.value}% or +${fields.takeProfitPercent.value}%`
    : "Auto-sell is off";
  fields.autopilotLastAction.textContent = state.last_action || "No autopilot action yet.";
}

function renderBacktestResult(result) {
  const pnlClass = result.pnl_percent >= 0 ? "positive" : "negative";
  fields.backtestPnl.textContent = `${Number(result.pnl_percent).toFixed(2)}%`;
  fields.backtestPnl.className = pnlClass;
  fields.backtestEquity.textContent = money(result.ending_equity);
  fields.backtestTrades.textContent = result.trade_count;
  fields.backtestWinRate.textContent = `${Number(result.win_rate).toFixed(1)}%`;
  fields.backtestVerdict.textContent = result.is_profitable ? "Profitable" : "Not Valid";
  fields.backtestVerdict.className = `status-pill ${result.is_profitable ? "ok" : "error"}`;
  fields.backtestSummary.textContent =
    `${result.trade_count} trade(s), ${money(result.pnl)} total PnL`;
}

function percent(value) {
  if (value === null || value === undefined) {
    return "Needs candles";
  }
  return `${Number(value).toFixed(1)}%`;
}

function renderStrategies(strategies) {
  const selected = strategies.find((item) => item.selected) || strategies[0];
  if (selected) {
    fields.selectedStrategyBadge.textContent = selected.name;
    fields.selectedStrategyBadge.className = "status-pill ok";
    fields.strategySummary.textContent =
      `${selected.name} drives paper autopilot when it is running.`;
    fields.backtestStrategySelect.value = selected.id;
  }

  fields.strategyList.innerHTML = strategies
    .map((strategy) => {
      const selectedClass = strategy.selected ? " selected" : "";
      const disabled = strategy.selected ? "disabled" : "";
      return `
        <article class="strategy-card${selectedClass}">
          <div class="strategy-card-head">
            <div>
              <strong>${strategy.name}</strong>
              <span>${strategy.description}</span>
            </div>
            <span class="strategy-rate">${percent(strategy.success_rate)}</span>
          </div>
          <div class="strategy-stats">
            <span>Avg PnL: ${percent(strategy.average_pnl_percent)}</span>
            <span>Symbols tested: ${strategy.tested_symbols}</span>
          </div>
          <div class="strategy-columns">
            <div>
              <b>Pros</b>
              <ul>${strategy.pros.map((item) => `<li>${item}</li>`).join("")}</ul>
            </div>
            <div>
              <b>Cons</b>
              <ul>${strategy.cons.map((item) => `<li>${item}</li>`).join("")}</ul>
            </div>
          </div>
          <button type="button" data-strategy-id="${strategy.id}" ${disabled}>
            ${strategy.selected ? "Selected" : "Select Model"}
          </button>
        </article>
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

function symbolSeed(symbol) {
  return symbol.split("").reduce((total, letter) => total + letter.charCodeAt(0), 0);
}

function candleCacheKey(symbol, timeframe = activeChartTimeframe) {
  return `${symbol.toUpperCase()}::${timeframe}`;
}

function activeTimeframe() {
  return timeframeConfig[activeChartTimeframe] || timeframeConfig["1m"];
}

function generateDemoCandles(symbol, timeframe = activeChartTimeframe) {
  const config = timeframeConfig[timeframe] || timeframeConfig["1m"];
  const seed = symbolSeed(symbol);
  let price = 80 + (seed % 90);
  const now = Date.now();
  const candles = [];

  for (let index = 0; index < config.count; index += 1) {
    const wave = Math.sin((index + seed) / 4) * 1.7;
    const drift = Math.cos((index + seed) / 9) * 0.8;
    const open = price;
    const close = Math.max(1, open + wave + drift);
    const high = Math.max(open, close) + 0.6 + ((index + seed) % 5) * 0.18;
    const low = Math.max(0.01, Math.min(open, close) - 0.6 - ((index + seed) % 4) * 0.16);
    price = close;
    candles.push({
      symbol,
      timestamp: new Date(now - (config.count - index) * config.ms).toISOString(),
      open,
      high,
      low,
      close,
      volume: 900 + ((index + seed) % 24) * 85,
    });
  }

  return candles;
}

async function loadCandles(symbol) {
  const normalizedSymbol = symbol.toUpperCase();
  const key = candleCacheKey(normalizedSymbol);
  try {
    const candles = await request(`/candles/${normalizedSymbol}`);
    if (candles.length && activeChartTimeframe === "1m") {
      localCandleCache.set(key, candles);
      return candles;
    }
  } catch (error) {
    setConnection("warning", "Demo chart");
  }

  if (!localCandleCache.has(key)) {
    localCandleCache.set(key, generateDemoCandles(normalizedSymbol));
  }
  return localCandleCache.get(key);
}

async function renderWatchlist() {
  const rows = await Promise.all(
    watchlistSymbols.map(async (symbol) => {
      const candles = await loadCandles(symbol);
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

function priceY(value, min, max, height, padding) {
  const range = max - min || 1;
  return height - padding - ((value - min) / range) * (height - padding * 2);
}

function formatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  if (activeChartTimeframe === "1d") {
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  }
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
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
  const padding = 52;
  const closes = displayCandles.map((candle) => Number(candle.close));
  const highs = displayCandles.map((candle) => Number(candle.high));
  const lows = displayCandles.map((candle) => Number(candle.low));
  const volumes = displayCandles.map((candle) => Number(candle.volume || 0));
  const minPrice = Math.min(...lows);
  const maxPrice = Math.max(...highs);
  const maValues = movingAverage(closes, 5);
  const maxVolume = Math.max(...volumes, 1);

  context.strokeStyle = "#222b3a";
  context.lineWidth = 1;
  context.beginPath();
  for (let index = 0; index < 6; index += 1) {
    const y = padding + ((height - padding * 2) / 5) * index;
    context.moveTo(padding, y);
    context.lineTo(width - padding, y);
  }
  for (let index = 0; index < 8; index += 1) {
    const x = padding + ((width - padding * 2) / 7) * index;
    context.moveTo(x, padding);
    context.lineTo(x, height - padding);
  }
  context.stroke();

  const candleSlot = (width - padding * 2) / Math.max(displayCandles.length, 1);
  const bodyWidth = Math.max(5, Math.min(18, candleSlot * 0.62));

  displayCandles.forEach((candle, index) => {
    const volume = volumes[index];
    const open = Number(candle.open);
    const close = Number(candle.close);
    const high = Number(candle.high);
    const low = Number(candle.low);
    const x = padding + candleSlot * index + candleSlot / 2;
    const openY = priceY(open, minPrice, maxPrice, height, padding);
    const closeY = priceY(close, minPrice, maxPrice, height, padding);
    const highY = priceY(high, minPrice, maxPrice, height, padding);
    const lowY = priceY(low, minPrice, maxPrice, height, padding);
    const isUp = close >= open;
    const color = isUp ? "#26a69a" : "#ef5350";
    const bodyTop = Math.min(openY, closeY);
    const bodyHeight = Math.max(2, Math.abs(closeY - openY));
    const barHeight = (volume / maxVolume) * 54;

    context.fillStyle = isUp ? "rgba(38, 166, 154, 0.18)" : "rgba(239, 83, 80, 0.18)";
    context.fillRect(x - bodyWidth / 2, height - padding - barHeight, bodyWidth, barHeight);

    context.strokeStyle = color;
    context.lineWidth = 1.4 * (window.devicePixelRatio || 1);
    context.beginPath();
    context.moveTo(x, highY);
    context.lineTo(x, lowY);
    context.stroke();

    if (isUp) {
      context.strokeStyle = color;
      context.strokeRect(x - bodyWidth / 2, bodyTop, bodyWidth, bodyHeight);
    } else {
      context.fillStyle = color;
      context.fillRect(x - bodyWidth / 2, bodyTop, bodyWidth, bodyHeight);
    }
  });

  context.strokeStyle = "#fbc02d";
  context.lineWidth = 1.8 * (window.devicePixelRatio || 1);
  context.beginPath();
  maValues.forEach((value, index) => {
    const x = padding + candleSlot * index + candleSlot / 2;
    const y = priceY(value, minPrice, maxPrice, height, padding);
    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });
  context.stroke();

  const lastCloseY = priceY(closes.at(-1), minPrice, maxPrice, height, padding);
  context.setLineDash([6, 6]);
  context.strokeStyle = "#2962ff";
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(padding, lastCloseY);
  context.lineTo(width - padding, lastCloseY);
  context.stroke();
  context.setLineDash([]);

  context.fillStyle = "#c9d7eb";
  context.font = `${13 * (window.devicePixelRatio || 1)}px Segoe UI, Arial`;
  context.fillText(money(maxPrice), 8, padding + 4);
  context.fillText(money(minPrice), 8, height - padding + 4);

  const labelIndexes = [0, Math.floor((displayCandles.length - 1) / 2), displayCandles.length - 1];
  context.fillStyle = "#94a9c6";
  context.font = `${12 * (window.devicePixelRatio || 1)}px Segoe UI, Arial`;
  labelIndexes.forEach((index) => {
    const candle = displayCandles[index];
    if (!candle) {
      return;
    }
    const x = padding + candleSlot * index + candleSlot / 2;
    const label = formatTimestamp(candle.timestamp);
    context.fillText(label, Math.min(x, width - padding - 56), height - 18);
  });

  fields.chartTitle.textContent = symbol;
  fields.chartSummary.textContent = `${displayCandles.length}/${candles.length} candles | ${activeTimeframe().label} interval`;
  fields.chartLast.textContent = money(closes.at(-1));
  fields.chartHigh.textContent = money(maxPrice);
  fields.chartLow.textContent = money(minPrice);
  fields.chartVolume.textContent = volumes.at(-1).toLocaleString();
}

async function loadChart(symbol = activeChartSymbol) {
  activeChartSymbol = symbol.toUpperCase();
  const candles = await loadCandles(activeChartSymbol);
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
  const normalizedSymbol = symbol.toUpperCase();
  const candles = generateDemoCandles(normalizedSymbol, activeChartTimeframe);
  localCandleCache.set(candleCacheKey(normalizedSymbol), candles);

  for (const candle of candles.slice(-24)) {
    try {
      await request("/candles", {
        method: "POST",
        body: JSON.stringify(candle),
      });
    } catch (error) {
      setConnection("warning", "Demo chart");
      break;
    }
  }
}

async function addLiveTick(symbol) {
  const candles = await loadCandles(symbol);
  const previous = candles.length ? Number(candles.at(-1).close) : 100 + Math.random() * 12;
  const previousTimestamp = candles.length
    ? new Date(candles.at(-1).timestamp).getTime()
    : Date.now();
  const nextTimestamp = previousTimestamp + activeTimeframe().ms;
  const move = (Math.random() - 0.48) * 2.1;
  const open = previous;
  const close = Math.max(1, previous + move);
  const high = Math.max(open, close) + Math.random() * 0.75;
  const low = Math.max(0.01, Math.min(open, close) - Math.random() * 0.75);
  const candle = {
    symbol: symbol.toUpperCase(),
    timestamp: new Date(nextTimestamp).toISOString(),
    open,
    high,
    low,
    close,
    volume: 1200 + Math.round(Math.random() * 1800),
  };
  const updatedCandles = [...candles, candle].slice(-120);
  localCandleCache.set(candleCacheKey(candle.symbol), updatedCandles);

  try {
    await request("/candles", {
      method: "POST",
      body: JSON.stringify(candle),
    });
  } catch (error) {
    setConnection("warning", "Demo chart");
  }
}

async function refreshDashboard() {
  const [status, portfolio, trades, sellDecisions, autopilot, strategies] = await Promise.all([
    request("/status"),
    request("/portfolio"),
    request("/trades"),
    request("/sell-decisions"),
    request("/autopilot"),
    request("/strategies"),
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
  renderAutopilot(autopilot);
  renderStrategies(strategies);
  renderMetricSparklines(portfolio, status);
  await loadChart(activeChartSymbol);
  await renderWatchlist();
  setConnection("ok", "Connected");
  showActivity("Dashboard refreshed", { status, portfolio, trades, sellDecisions, autopilot });
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

document.querySelectorAll(".timeframe-button").forEach((button) => {
  button.addEventListener("click", async () => {
    document.querySelectorAll(".timeframe-button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    activeChartTimeframe = button.dataset.timeframe;
    await loadChart(activeChartSymbol);
    await renderWatchlist();
    showActivity("Chart interval changed", {
      interval: activeTimeframe().label,
    });
  });
});

fields.strategyList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-strategy-id]");
  if (!button) {
    return;
  }

  try {
    const state = await request("/strategies/select", {
      method: "POST",
      body: JSON.stringify({ strategy_id: button.dataset.strategyId }),
    });
    renderAutopilot(state);
    renderStrategies(await request("/strategies"));
    showActivity("Strategy model selected", state);
  } catch (error) {
    showActivity("Strategy select failed", { error: error.message });
  }
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

document.querySelector("#backtestForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = {
    symbol: String(form.get("symbol")).toUpperCase(),
    starting_cash: Number(form.get("starting_cash")),
    quantity: Number(form.get("quantity")),
    short_window: Number(form.get("short_window")),
    long_window: Number(form.get("long_window")),
    strategy_id: String(form.get("strategy_id")),
  };

  try {
    const result = await request("/backtest", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderBacktestResult(result);
    showActivity("Backtest complete", result);
  } catch (error) {
    fields.backtestVerdict.textContent = "No Result";
    fields.backtestVerdict.className = "status-pill error";
    fields.backtestSummary.textContent = error.message;
    showActivity("Backtest failed", { error: error.message });
  }
});

async function runAutopilotTick() {
  const state = await request("/autopilot/tick", { method: "POST", body: "{}" });
  renderAutopilot(state);
  await refreshDashboard();
  return state;
}

document.querySelector("#saveAutopilotConfigButton").addEventListener("click", async () => {
  const stopLossPercent = Number(fields.stopLossPercent.value);
  const takeProfitPercent = Number(fields.takeProfitPercent.value);

  if (stopLossPercent <= 0 || takeProfitPercent <= 0) {
    showActivity("Sell rules need positive percentages", {
      error: "Use values greater than 0.",
    });
    return;
  }

  try {
    const state = await request("/autopilot/config", {
      method: "POST",
      body: JSON.stringify({
        auto_sell_enabled: fields.autoSellToggle.checked,
        stop_loss_percent: stopLossPercent / 100,
        take_profit_percent: takeProfitPercent / 100,
      }),
    });
    renderAutopilot(state);
    showActivity("Auto-sell rules saved", state);
  } catch (error) {
    showActivity("Auto-sell save failed", { error: error.message });
  }
});

function startAutopilotTimer() {
  clearInterval(autopilotTimer);
  autopilotTimer = setInterval(() => {
    runAutopilotTick().catch((error) => {
      setConnection("error", "Offline");
      showActivity("Autopilot failed", { error: error.message });
    });
  }, 6000);
}

function stopAutopilotTimer() {
  clearInterval(autopilotTimer);
}

document.querySelector("#startAutopilotButton").addEventListener("click", async () => {
  try {
    const state = await request("/autopilot/start", {
      method: "POST",
      body: JSON.stringify({ symbols: watchlistSymbols }),
    });
    renderAutopilot(state);
    startAutopilotTimer();
    showActivity("Paper autopilot started", state);
  } catch (error) {
    showActivity("Autopilot start failed", { error: error.message });
  }
});

document.querySelector("#stopAutopilotButton").addEventListener("click", async () => {
  try {
    const state = await request("/autopilot/stop", { method: "POST", body: "{}" });
    stopAutopilotTimer();
    renderAutopilot(state);
    showActivity("Paper autopilot stopped", state);
  } catch (error) {
    showActivity("Autopilot stop failed", { error: error.message });
  }
});

document.querySelector("#runAutopilotButton").addEventListener("click", async () => {
  try {
    const state = await runAutopilotTick();
    showActivity("Autopilot checked markets", state);
  } catch (error) {
    showActivity("Autopilot check failed", { error: error.message });
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
    chart_interval: activeTimeframe().label,
  });
});

window.addEventListener("resize", () => {
  loadChart(activeChartSymbol).catch(() => undefined);
  drawSparkline(fields.cashSparkline, metricHistory.cash, "#38bdf8");
  drawSparkline(fields.equitySparkline, metricHistory.equity, "#60a5fa");
  drawSparkline(fields.positionsSparkline, metricHistory.positions, "#93c5fd");
  drawSparkline(fields.plSparkline, metricHistory.pl, "#5eead4");
});

refreshDashboard().catch(async (error) => {
  setConnection("error", "Offline");
  showActivity("Backend unavailable", {
    error: error.message,
    hint: "Start the API with: python -m uvicorn trading_bot.app:app --reload",
  });
  await loadChart(activeChartSymbol);
  await renderWatchlist();
});
startLiveRefresh();
startLiveMarket();
