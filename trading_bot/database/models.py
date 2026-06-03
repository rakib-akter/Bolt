from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TradeRecord:
    symbol: str
    side: str
    quantity: float
    price: float
    status: str
    created_at: datetime
    message: str = ""
    id: int | None = None

