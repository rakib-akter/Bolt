from datetime import UTC, datetime
import sqlite3
from pathlib import Path

from trading_bot.broker.base_broker import OrderResult
from trading_bot.database.models import TradeRecord


SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
"""


class TradeRepository:
    def __init__(self, database_path: str | Path = "tradebot.sqlite3") -> None:
        self.database_path = Path(database_path)
        self.initialize()

    def initialize(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(SCHEMA)

    def save_order_result(self, result: OrderResult) -> TradeRecord:
        record = TradeRecord(
            symbol=result.symbol,
            side=result.side,
            quantity=result.quantity,
            price=result.price,
            status=result.status,
            message=result.message,
            created_at=datetime.now(UTC),
        )
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO trades
                    (symbol, side, quantity, price, status, message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.symbol,
                    record.side,
                    record.quantity,
                    record.price,
                    record.status,
                    record.message,
                    record.created_at.isoformat(),
                ),
            )
            trade_id = int(cursor.lastrowid)
        return TradeRecord(**{**record.__dict__, "id": trade_id})

    def list_trades(self) -> list[TradeRecord]:
        with sqlite3.connect(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, symbol, side, quantity, price, status, message, created_at
                FROM trades
                ORDER BY id ASC
                """
            ).fetchall()

        return [
            TradeRecord(
                id=row[0],
                symbol=row[1],
                side=row[2],
                quantity=row[3],
                price=row[4],
                status=row[5],
                message=row[6],
                created_at=datetime.fromisoformat(row[7]),
            )
            for row in rows
        ]

    def clear(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("DELETE FROM trades")
