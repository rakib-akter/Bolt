from trading_bot.broker.base_broker import BaseBroker, OrderResult, OrderSide, Position


class PaperBroker(BaseBroker):
    def __init__(self, cash: float, prices: dict[str, float] | None = None) -> None:
        self.starting_cash = cash
        self.cash = cash
        self.prices = prices or {}
        self.positions: dict[str, Position] = {}

    def reset(self, cash: float | None = None) -> None:
        self.cash = cash if cash is not None else self.starting_cash
        self.positions.clear()

    def set_price(self, symbol: str, price: float) -> None:
        if price <= 0:
            raise ValueError("Price must be greater than zero.")
        self.prices[symbol.upper()] = price

    def get_balance(self) -> float:
        return self.cash

    def get_price(self, symbol: str) -> float:
        normalized_symbol = symbol.upper()
        if normalized_symbol not in self.prices:
            raise KeyError(f"No paper price configured for {normalized_symbol}.")
        return self.prices[normalized_symbol]

    def place_order(
        self, symbol: str, side: OrderSide, quantity: float
    ) -> OrderResult:
        if quantity <= 0:
            return OrderResult(symbol, side, quantity, 0, "rejected", "Invalid quantity.")

        normalized_symbol = symbol.upper()
        price = self.get_price(normalized_symbol)
        notional = price * quantity

        if side == "buy":
            if notional > self.cash:
                return OrderResult(
                    normalized_symbol,
                    side,
                    quantity,
                    price,
                    "rejected",
                    "Insufficient paper cash.",
                )
            self.cash -= notional
            self._increase_position(normalized_symbol, quantity, price)
            return OrderResult(normalized_symbol, side, quantity, price, "filled")

        if side == "sell":
            position = self.positions.get(normalized_symbol)
            if position is None or position.quantity < quantity:
                return OrderResult(
                    normalized_symbol,
                    side,
                    quantity,
                    price,
                    "rejected",
                    "Insufficient paper position.",
                )
            self.cash += notional
            self._decrease_position(normalized_symbol, quantity)
            return OrderResult(normalized_symbol, side, quantity, price, "filled")

        return OrderResult(normalized_symbol, side, quantity, price, "rejected", "Bad side.")

    def get_positions(self) -> list[Position]:
        return list(self.positions.values())

    def _increase_position(self, symbol: str, quantity: float, price: float) -> None:
        existing = self.positions.get(symbol)
        if existing is None:
            self.positions[symbol] = Position(symbol, quantity, price)
            return

        total_quantity = existing.quantity + quantity
        total_cost = existing.average_price * existing.quantity + price * quantity
        self.positions[symbol] = Position(symbol, total_quantity, total_cost / total_quantity)

    def _decrease_position(self, symbol: str, quantity: float) -> None:
        existing = self.positions[symbol]
        remaining_quantity = existing.quantity - quantity
        if remaining_quantity == 0:
            del self.positions[symbol]
            return
        self.positions[symbol] = Position(
            symbol, remaining_quantity, existing.average_price
        )
