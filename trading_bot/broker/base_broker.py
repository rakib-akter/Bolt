from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

OrderSide = Literal["buy", "sell"]


@dataclass(frozen=True)
class OrderResult:
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    status: str
    message: str = ""


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    average_price: float


class BaseBroker(ABC):
    @abstractmethod
    def get_balance(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_price(self, symbol: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def place_order(
        self, symbol: str, side: OrderSide, quantity: float
    ) -> OrderResult:
        raise NotImplementedError

    @abstractmethod
    def get_positions(self) -> list[Position]:
        raise NotImplementedError

