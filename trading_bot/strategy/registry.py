from collections.abc import Callable
from dataclasses import dataclass

from trading_bot.strategy.base_strategy import BaseStrategy
from trading_bot.strategy.breakout_strategy import BreakoutStrategy
from trading_bot.strategy.momentum_strategy import MomentumStrategy
from trading_bot.strategy.moving_average_strategy import MovingAverageStrategy
from trading_bot.strategy.rsi_strategy import RsiMeanReversionStrategy


@dataclass(frozen=True)
class StrategyDefinition:
    id: str
    name: str
    description: str
    pros: list[str]
    cons: list[str]
    factory: Callable[[], BaseStrategy]


STRATEGIES = {
    "moving_average": StrategyDefinition(
        id="moving_average",
        name="Moving Average Trend",
        description="Follows trend direction when the short average is above or below the long average.",
        pros=[
            "Easy to understand",
            "Works best in sustained trends",
            "Filters out some short-term noise",
        ],
        cons=[
            "Can react late after price already moved",
            "Can chop in sideways markets",
        ],
        factory=lambda: MovingAverageStrategy(short_window=5, long_window=20),
    ),
    "momentum": StrategyDefinition(
        id="momentum",
        name="Momentum Burst",
        description="Buys strong recent upward moves and sells sharp downward moves.",
        pros=[
            "Fast to react",
            "Good for active, directional markets",
            "Simple entry and exit logic",
        ],
        cons=[
            "Can chase moves after they are stretched",
            "Needs risk controls during reversals",
        ],
        factory=lambda: MomentumStrategy(lookback=5, threshold_percent=0.02),
    ),
    "breakout": StrategyDefinition(
        id="breakout",
        name="Breakout",
        description="Buys when price closes above recent resistance and sells below recent support.",
        pros=[
            "Captures range breaks",
            "Good when volatility expands",
            "Uses clear support and resistance levels",
        ],
        cons=[
            "False breakouts can trigger bad entries",
            "May stay inactive during quiet markets",
        ],
        factory=lambda: BreakoutStrategy(lookback=20),
    ),
    "rsi_reversion": StrategyDefinition(
        id="rsi_reversion",
        name="RSI Mean Reversion",
        description="Buys oversold conditions and sells overbought conditions using RSI.",
        pros=[
            "Good for range-bound markets",
            "Avoids buying when RSI is already overheated",
            "Clear overbought and oversold rules",
        ],
        cons=[
            "Can fight strong trends too early",
            "Needs stop losses when momentum keeps moving against it",
        ],
        factory=lambda: RsiMeanReversionStrategy(window=14),
    ),
}


def create_strategy(strategy_id: str) -> BaseStrategy:
    try:
        return STRATEGIES[strategy_id].factory()
    except KeyError as exc:
        raise ValueError(f"Unknown strategy: {strategy_id}.") from exc
