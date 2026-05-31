from __future__ import annotations


def format_int(value: float | int | None) -> str:
    if value is None:
        return "0"
    return f"{int(round(float(value))):,}".replace(",", ".")


def format_currency(value: float | int | None) -> str:
    if value is None:
        return "R$ 0"
    number = float(value)
    abs_value = abs(number)
    if abs_value >= 1_000_000_000:
        formatted = (
            f"{number / 1_000_000_000:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        return f"R$ {formatted} bi"
    if abs_value >= 1_000_000:
        formatted = (
            f"{number / 1_000_000:,.1f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        return f"R$ {formatted} mi"
    formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def format_percent(value: float | int | None) -> str:
    if value is None:
        return "0,0%"
    return f"{float(value) * 100:.1f}%".replace(".", ",")
