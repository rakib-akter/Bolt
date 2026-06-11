from collections.abc import Sequence


def simple_moving_average(values: Sequence[float], window: int) -> float:
    if window <= 0:
        raise ValueError("Window must be greater than zero.")
    if len(values) < window:
        raise ValueError("Not enough values for moving average window.")
    return sum(values[-window:]) / window


def closes_from_candles(candles: Sequence[object]) -> list[float]:
    return [float(candle.close) for candle in candles]


def relative_strength_index(values: Sequence[float], window: int = 14) -> float:
    if window <= 0:
        raise ValueError("Window must be greater than zero.")
    if len(values) <= window:
        raise ValueError("Not enough values for RSI window.")

    gains: list[float] = []
    losses: list[float] = []
    for index in range(len(values) - window, len(values)):
        change = values[index] - values[index - 1]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))

    average_gain = sum(gains) / window
    average_loss = sum(losses) / window
    if average_loss == 0:
        return 100.0

    relative_strength = average_gain / average_loss
    return 100 - (100 / (1 + relative_strength))
