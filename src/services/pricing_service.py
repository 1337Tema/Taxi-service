"""
Сервис для расчёта цены и ETA поездки.

Формулы:
    distance = |x1 - x2| + |y1 - y2|
    eta_seconds = distance * T_CELL
    price = BASE_FARE + distance * PRICE_PER_CELL

Значения берутся из src.core.config.settings (поля, добавленные ниже).
"""

from typing import TypedDict

from src.core.config import settings


class PricingResult(TypedDict):
    distance: int
    eta_seconds: float
    price: float


def calculate_price_and_eta(start_x: int, start_y: int, end_x: int, end_y: int) -> PricingResult:
    """
    Рассчитать расстояние (в ячейках), ETA и цену.
    Возвращает словарь с полями: distance, eta_seconds, price.
    """
    dx = abs(start_x - end_x)
    dy = abs(start_y - end_y)
    distance = dx + dy

    eta_seconds = distance * float(settings.PRICE_T_CELL)
    price = float(settings.PRICE_BASE_FARE) + distance * float(settings.PRICE_PER_CELL)

    return PricingResult(distance=distance, eta_seconds=eta_seconds, price=price)
