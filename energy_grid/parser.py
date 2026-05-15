"""JSON parsing utilities for the energy grid simulator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Consumer, Generator

__all__ = ["load_input"]

_EXPECTED_HOURS = 24


def _is_non_negative_number(value: object) -> bool:
    """Return True when value is an int or float, but not bool, and is >= 0."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def _validate_number_list(values: Any, field_name: str) -> list[float]:
    """Validate an hourly numeric list and normalize it to floats."""
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list")
    if len(values) != _EXPECTED_HOURS:
        raise ValueError(f"{field_name} must contain exactly {_EXPECTED_HOURS} values")
    if not all(_is_non_negative_number(value) for value in values):
        raise ValueError(f"{field_name} must contain only non-negative numbers")
    return [float(value) for value in values]


def _validate_non_empty_string(value: Any, field_name: str) -> str:
    """Validate that a field is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _validate_unique_names(items: list[dict[str, Any]], field_name: str) -> None:
    """Validate that entity names are unique within a section."""
    names = [item["name"] for item in items]
    if len(names) != len(set(names)):
        raise ValueError(f"{field_name} names must be unique")


def _parse_consumers(raw_consumers: Any) -> list[Consumer]:
    """Validate and parse consumers."""
    if not isinstance(raw_consumers, list) or not raw_consumers:
        raise ValueError("The 'consumers' field must be a non-empty list")

    normalized_items: list[dict[str, Any]] = []
    for index, item in enumerate(raw_consumers):
        if not isinstance(item, dict):
            raise ValueError(f"Consumer at index {index} must be an object")

        name = _validate_non_empty_string(item.get("name"), f"Consumer name at index {index}")
        demand = _validate_number_list(item.get("demand"), f"Consumer demand for '{name}'")
        normalized_items.append({"name": name, "demand": demand})

    _validate_unique_names(normalized_items, "Consumer")
    return [Consumer(name=item["name"], demand=item["demand"]) for item in normalized_items]


def _parse_generators(raw_generators: Any) -> list[Generator]:
    """Validate and parse generators."""
    if not isinstance(raw_generators, list) or not raw_generators:
        raise ValueError("The 'generators' field must be a non-empty list")

    normalized_items: list[dict[str, Any]] = []
    for index, item in enumerate(raw_generators):
        if not isinstance(item, dict):
            raise ValueError(f"Generator at index {index} must be an object")

        name = _validate_non_empty_string(item.get("name"), f"Generator name at index {index}")
        kind = _validate_non_empty_string(item.get("kind"), f"Generator kind for '{name}'")
        generation = _validate_number_list(
            item.get("generation"),
            f"Generator generation for '{name}'",
        )
        cost_per_unit = item.get("cost_per_unit")
        if not _is_non_negative_number(cost_per_unit):
            raise ValueError(f"Generator cost_per_unit for '{name}' must be a non-negative number")

        normalized_items.append(
            {
                "name": name,
                "kind": kind,
                "generation": generation,
                "cost_per_unit": float(cost_per_unit),
            }
        )

    _validate_unique_names(normalized_items, "Generator")
    return [
        Generator(
            name=item["name"],
            kind=item["kind"],
            generation=item["generation"],
            cost_per_unit=item["cost_per_unit"],
        )
        for item in normalized_items
    ]


def load_input(path: str | Path) -> tuple[list[Consumer], list[Generator]]:
    """Load and validate consumers and generators from JSON."""
    input_path = Path(path)

    try:
        with input_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in '{input_path}': {error.msg}") from error

    if not isinstance(data, dict):
        raise ValueError("Top-level JSON value must be an object")

    consumers = _parse_consumers(data.get("consumers"))
    generators = _parse_generators(data.get("generators"))
    return consumers, generators
