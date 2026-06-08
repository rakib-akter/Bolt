const API_BASE = "http://127.0.0.1:8000";

const fields = {
  environment: document.querySelector("#environment"),
  broker: document.querySelector("#broker"),
  cash: document.querySelector("#cash"),
  positions: document.querySelector("#positions"),
  activity: document.querySelector("#activity"),
};

function showActivity(value) {
  fields.activity.textContent = JSON.stringify(value, null, 2);
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

async function refreshDashboard() {
  const [status, portfolio, trades] = await Promise.all([
    request("/status"),
    request("/portfolio"),
    request("/trades"),
  ]);

  fields.environment.textContent = status.environment;
  fields.broker.textContent = status.broker;
  fields.cash.textContent = `$${Number(portfolio.cash).toFixed(2)}`;
  fields.positions.textContent = status.position_count;
  showActivity({ status, portfolio, trades });
}

document.querySelector("#refreshButton").addEventListener("click", () => {
  refreshDashboard().catch((error) => showActivity({ error: error.message }));
});

document.querySelector("#candleForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const close = Number(form.get("close"));
  const payload = {
    symbol: form.get("symbol"),
    open: close,
    high: close,
    low: close,
    close,
    volume: 100,
  };
  try {
    const result = await request("/candles", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showActivity(result);
    await refreshDashboard();
  } catch (error) {
    showActivity({ error: error.message });
  }
});

document.querySelector("#runForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = {
    symbol: form.get("symbol"),
    stop_loss: Number(form.get("stopLoss")),
  };
  try {
    const result = await request("/run-once", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showActivity(result);
    await refreshDashboard();
  } catch (error) {
    showActivity({ error: error.message });
  }
});

refreshDashboard().catch((error) => showActivity({ error: error.message }));

