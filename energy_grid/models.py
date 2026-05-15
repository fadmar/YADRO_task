"""Data models for the energy grid simulator."""

from dataclasses import dataclass

__all__ = ["Consumer", "Generator", "HourSchedule"]


@dataclass
class Consumer:
    name: str
    demand: list[float]


@dataclass
class Generator:
    name: str
    kind: str
    generation: list[float]
    cost_per_unit: float


@dataclass
class HourSchedule:
    hour: int
    enabled_generators: list[str]
    enabled_consumers: list[str]
    disabled_consumers: list[str]
    total_demand: float
    served_demand: float
    total_generation: float
    cost: float
    excess_energy: float
    shortage: bool
