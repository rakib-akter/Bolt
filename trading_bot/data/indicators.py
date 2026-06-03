from collections.abc import Sequence


def simple_moving_average(values: Sequence[float], window: int) -> float:
    if window <= 0:
        raise ValueError("Window must be greater than zero.")
    if len(values) < window:
        raise ValueError("Not enough values for moving average window.")
    return sum(values[-window:]) / window


def closes_from_candles(candles: Sequence[object]) -> list[float]:
    return [float(candle.close) for candle in candles]

