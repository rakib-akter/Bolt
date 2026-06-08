import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from trading_bot.broker.base_broker import BaseBroker, OrderResult, OrderSide, Position


class AlpacaBroker(BaseBroker):
    """Small Alpaca paper-trading API wrapper.

    The app defaults to PaperBroker. Use this wrapper only after setting paper
    credentials in environment variables.
    """

    def __init__(self, api_key: str, secret_key: str, base_url: str) -> None:
        if not api_key or not secret_key:
            raise ValueError("Alpaca API key and secret are required.")
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip("/")

    def get_balance(self) -> float:
        account = self._request("GET", "/v2/account")
        return float(account["cash"])

    def get_price(self, symbol: str) -> float:
        raise NotImplementedError("Market data price lookup is not wired yet.")

    def place_order(
        self, symbol: str, side: OrderSide, quantity: float
    ) -> OrderResult:
        payload = {
            "symbol": symbol.upper(),
            "qty": str(quantity),
            "side": side,
            "type": "market",
            "time_in_force": "day",
        }
        response = self._request("POST", "/v2/orders", payload)
        filled_price = float(response.get("filled_avg_price") or 0)
        return OrderResult(
            symbol=response["symbol"],
            side=side,
            quantity=float(response["qty"]),
            price=filled_price,
            status=response["status"],
            message=response.get("id", ""),
        )

    def get_positions(self) -> list[Position]:
        response = self._request("GET", "/v2/positions")
        return [
            Position(
                symbol=item["symbol"],
                quantity=float(item["qty"]),
                average_price=float(item["avg_entry_price"]),
            )
            for item in response
        ]

    def _request(
        self, method: str, path: str, payload: dict[str, str] | None = None
    ) -> dict[str, object] | list[dict[str, object]]:
        body = json.dumps(payload).encode("utf-8") if payload else None
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8")
            raise RuntimeError(f"Alpaca request failed: {detail}") from exc

