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
    realized_pl: float = 0.0


@dataclass(frozen=True)
class BacktestResult:
    starting_cash: float
    ending_cash: float
    ending_position: float
    ending_equity: float
    pnl: float
    pnl_percent: float
    trade_count: int
    winning_trades: int
    win_rate: float
    is_profitable: bool
    trades: list[BacktestTrade]


class BacktestEngine:
    def __init__(self, strategy: BaseStrategy, starting_cash: float = 10000.0) -> None:
        self.strategy = strategy
        self.starting_cash = starting_cash

    def run(self, candles: list[Candle], quantity: float = 1.0) -> BacktestResult:
        cash = self.starting_cash
        position = 0.0
        average_entry = 0.0
        trades: list[BacktestTrade] = []
        winning_trades = 0

        for index in range(1, len(candles) + 1):
            window = candles[:index]
            signal = self.strategy.generate_signal(window)
            latest = window[-1]

            if signal == "BUY" and cash >= latest.close * quantity:
                cash -= latest.close * quantity
                total_cost = average_entry * position + latest.close * quantity
                position += quantity
                average_entry = total_cost / position
                trades.append(BacktestTrade(latest.symbol, signal, latest.close, cash, position))
            elif signal == "SELL" and position >= quantity:
                cash += latest.close * quantity
                realized_pl = (latest.close - average_entry) * quantity
                if realized_pl > 0:
                    winning_trades += 1
                position -= quantity
                if position == 0:
                    average_entry = 0.0
                trades.append(
                    BacktestTrade(
                        latest.symbol,
                        signal,
                        latest.close,
                        cash,
                        position,
                        realized_pl,
                    )
                )

        final_price = candles[-1].close if candles else 0
        ending_equity = cash + position * final_price
        pnl = ending_equity - self.starting_cash
        pnl_percent = pnl / self.starting_cash * 100 if self.starting_cash else 0.0
        trade_count = len(trades)
        sell_count = len([trade for trade in trades if trade.signal == "SELL"])
        return BacktestResult(
            starting_cash=self.starting_cash,
            ending_cash=cash,
            ending_position=position,
            ending_equity=ending_equity,
            pnl=pnl,
            pnl_percent=pnl_percent,
            trade_count=trade_count,
            winning_trades=winning_trades,
            win_rate=winning_trades / sell_count * 100 if sell_count else 0.0,
            is_profitable=pnl > 0,
            trades=trades,
        )
