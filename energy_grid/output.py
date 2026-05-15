"""Output formatting utilities for the energy grid simulator."""

from .models import HourSchedule

__all__ = ["format_schedule", "print_schedule"]


def _format_number(value: float) -> str:
    """Format a numeric value with two decimal places."""
    return f"{value:.2f}"


def _format_names(names: list[str]) -> str:
    """Format a list of names for table output."""
    if not names:
        return "-"
    return ", ".join(names)


def format_schedule(schedule: list[HourSchedule]) -> str:
    """Return a human-readable table for the hourly schedule."""
    headers = [
        "Hour",
        "Demand",
        "Served",
        "Generation",
        "Cost",
        "Excess",
        "Generators",
        "Disabled consumers",
    ]

    rows: list[list[str]] = []
    for hour_schedule in schedule:
        rows.append(
            [
                f"{hour_schedule.hour:02d}",
                _format_number(hour_schedule.total_demand),
                _format_number(hour_schedule.served_demand),
                _format_number(hour_schedule.total_generation),
                _format_number(hour_schedule.cost),
                _format_number(hour_schedule.excess_energy),
                _format_names(hour_schedule.enabled_generators),
                _format_names(hour_schedule.disabled_consumers),
            ]
        )

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    lines = [
        " | ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    ]
    for row in rows:
        lines.append(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))

    total_cost = sum(item.cost for item in schedule)
    hours_with_shortage = sum(1 for item in schedule if item.shortage)
    total_served_demand = sum(item.served_demand for item in schedule)
    total_generated_energy = sum(item.total_generation for item in schedule)

    lines.append("")
    lines.append(f"Total cost: {_format_number(total_cost)}")
    lines.append(f"Hours with shortage: {hours_with_shortage}")
    lines.append(f"Total served demand: {_format_number(total_served_demand)}")
    lines.append(f"Total generated energy: {_format_number(total_generated_energy)}")

    return "\n".join(lines)


def print_schedule(schedule: list[HourSchedule]) -> None:
    """Print the formatted schedule to stdout."""
    print(format_schedule(schedule))
