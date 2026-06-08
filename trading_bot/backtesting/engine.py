from dataclasses import dataclass

from trading_bot.data.market_data import Candle
from trading_bot.strategy.base_strategy import BaseStrategy, Signal


@dataclass(frozen=True)
class BacktestTrade:
    symbol: str
    signal: Signal
    price: float
    cash: float
    position: float


@dataclass(frozen=True)
class BacktestResult:
    starting_cash: float
    ending_cash: float
    ending_position: float
    ending_equity: float
    trades: list[BacktestTrade]


class BacktestEngine:
    def __init__(self, strategy: BaseStrategy, starting_cash: float = 10000.0) -> None:
        self.strategy = strategy
        self.starting_cash = starting_cash

    def run(self, candles: list[Candle], quantity: float = 1.0) -> BacktestResult:
        cash = self.starting_cash
        position = 0.0
        trades: list[BacktestTrade] = []

        for index in range(1, len(candles) + 1):
            window = candles[:index]
            signal = self.strategy.generate_signal(window)
            latest = window[-1]

            if signal == "BUY" and cash >= latest.close * quantity:
                cash -= latest.close * quantity
                position += quantity
                trades.append(BacktestTrade(latest.symbol, signal, latest.close, cash, position))
            elif signal == "SELL" and position >= quantity:
                cash += latest.close * quantity
                position -= quantity
                trades.append(BacktestTrade(latest.symbol, signal, latest.close, cash, position))

        final_price = candles[-1].close if candles else 0
        return BacktestResult(
            starting_cash=self.starting_cash,
            ending_cash=cash,
            ending_position=position,
            ending_equity=cash + position * final_price,
            trades=trades,
        )

