"""Scheduling helpers for the energy grid simulator."""

from itertools import combinations
from typing import Iterable, Sequence, TypeVar

from .models import Consumer, Generator, HourSchedule

__all__ = ["HOURS_PER_DAY", "powerset", "solve_hour", "build_schedule"]

HOURS_PER_DAY = 24

T = TypeVar("T")


def powerset(items: Sequence[T]) -> Iterable[tuple[T, ...]]:
    """Yield all subsets in deterministic order by increasing size."""
    for size in range(len(items) + 1):
        yield from combinations(items, size)


def _generation_at(generator: Generator, hour: int) -> float:
    """Return generator output for the given hour."""
    return generator.generation[hour]


def _generator_cost_at(generator: Generator, hour: int) -> float:
    """Return generator cost for the given hour."""
    return _generation_at(generator, hour) * generator.cost_per_unit


def _consumer_demand_at(consumer: Consumer, hour: int) -> float:
    """Return consumer demand for the given hour."""
    return consumer.demand[hour]


def _total_generation(generators: Sequence[Generator], hour: int) -> float:
    """Return total generation for a subset of generators."""
    return sum(_generation_at(generator, hour) for generator in generators)


def _total_generator_cost(generators: Sequence[Generator], hour: int) -> float:
    """Return total hourly cost for a subset of generators."""
    return sum(_generator_cost_at(generator, hour) for generator in generators)


def _total_served_demand(consumers: Sequence[Consumer], hour: int) -> float:
    """Return total served demand for a subset of consumers."""
    return sum(_consumer_demand_at(consumer, hour) for consumer in consumers)


def _names(items: Sequence[Consumer | Generator]) -> tuple[str, ...]:
    """Return item names in deterministic lexicographic order."""
    return tuple(sorted(item.name for item in items))


def solve_hour(
    consumers: list[Consumer],
    generators: list[Generator],
    hour: int,
) -> HourSchedule:
    """Find the optimal schedule for a single hour."""
    if hour < 0 or hour >= HOURS_PER_DAY:
        raise ValueError(f"Hour must be between 0 and {HOURS_PER_DAY - 1}: {hour}")

    total_demand = _total_served_demand(consumers, hour)
    all_consumer_names = list(_names(consumers))

    best_full_solution: tuple[tuple[float, float, int, tuple[str, ...]], tuple[Generator, ...]] | None = None

    for generator_subset in powerset(generators):
        total_generation = _total_generation(generator_subset, hour)
        if total_generation < total_demand:
            continue

        cost = _total_generator_cost(generator_subset, hour)
        excess_energy = total_generation - total_demand
        key = (
            cost,
            excess_energy,
            len(generator_subset),
            _names(generator_subset),
        )

        if best_full_solution is None or key < best_full_solution[0]:
            best_full_solution = (key, generator_subset)

    if best_full_solution is not None:
        enabled_generators = best_full_solution[1]
        total_generation = _total_generation(enabled_generators, hour)
        cost = _total_generator_cost(enabled_generators, hour)
        excess_energy = total_generation - total_demand
        return HourSchedule(
            hour=hour,
            enabled_generators=list(_names(enabled_generators)),
            enabled_consumers=all_consumer_names,
            disabled_consumers=[],
            total_demand=total_demand,
            served_demand=total_demand,
            total_generation=total_generation,
            cost=cost,
            excess_energy=excess_energy,
            shortage=False,
        )

    best_partial: tuple[
        int,
        float,
        float,
        float,
        int,
        tuple[str, ...],
        tuple[str, ...],
    ] | None = None
    best_consumer_subset: tuple[Consumer, ...] = ()
    best_generator_subset: tuple[Generator, ...] = ()

    for consumer_subset in powerset(consumers):
        served_demand = sum(_consumer_demand_at(consumer, hour) for consumer in consumer_subset)
        enabled_consumer_names = _names(consumer_subset)

        for generator_subset in powerset(generators):
            total_generation = sum(_generation_at(generator, hour) for generator in generator_subset)
            if total_generation < served_demand:
                continue

            cost = sum(_generator_cost_at(generator, hour) for generator in generator_subset)
            excess_energy = total_generation - served_demand
            key = (
                -len(consumer_subset),
                -served_demand,
                cost,
                excess_energy,
                len(generator_subset),
                enabled_consumer_names,
                _names(generator_subset),
            )

            if best_partial is None or key < best_partial:
                best_partial = key
                best_consumer_subset = consumer_subset
                best_generator_subset = generator_subset

    if best_partial is None:
        raise RuntimeError(f"Failed to find a feasible schedule for hour {hour}")

    enabled_consumer_name_set = set(_names(best_consumer_subset))
    disabled_consumers = sorted(
        consumer.name for consumer in consumers if consumer.name not in enabled_consumer_name_set
    )
    total_generation = _total_generation(best_generator_subset, hour)
    served_demand = _total_served_demand(best_consumer_subset, hour)
    cost = _total_generator_cost(best_generator_subset, hour)
    excess_energy = total_generation - served_demand

    return HourSchedule(
        hour=hour,
        enabled_generators=list(_names(best_generator_subset)),
        enabled_consumers=list(_names(best_consumer_subset)),
        disabled_consumers=disabled_consumers,
        total_demand=total_demand,
        served_demand=served_demand,
        total_generation=total_generation,
        cost=cost,
        excess_energy=excess_energy,
        shortage=True,
    )


def build_schedule(
    consumers: list[Consumer],
    generators: list[Generator],
) -> list[HourSchedule]:
    """Build the schedule for all 24 hours of the day."""
    return [solve_hour(consumers, generators, hour) for hour in range(HOURS_PER_DAY)]
