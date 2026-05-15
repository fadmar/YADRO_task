"""Tests for scheduler functionality."""

import unittest

from energy_grid.models import Consumer, Generator
from energy_grid.scheduler import build_schedule, solve_hour


class TestScheduler(unittest.TestCase):
    def test_cheapest_generator_is_selected(self) -> None:
        consumers = [Consumer(name="consumer_1", demand=[10] * 24)]
        generators = [
            Generator(name="expensive", kind="diesel", generation=[10] * 24, cost_per_unit=9),
            Generator(name="cheap", kind="diesel", generation=[10] * 24, cost_per_unit=3),
        ]

        result = solve_hour(consumers, generators, 0)

        self.assertEqual(result.enabled_generators, ["cheap"])
        self.assertEqual(result.disabled_consumers, [])
        self.assertFalse(result.shortage)

    def test_combination_of_generators_can_be_cheaper_than_one_large_generator(self) -> None:
        consumers = [Consumer(name="consumer_1", demand=[15] * 24)]
        generators = [
            Generator(name="small_a", kind="diesel", generation=[10] * 24, cost_per_unit=1),
            Generator(name="small_b", kind="diesel", generation=[10] * 24, cost_per_unit=1),
            Generator(name="large", kind="diesel", generation=[20] * 24, cost_per_unit=2),
        ]

        result = solve_hour(consumers, generators, 0)

        self.assertEqual(result.enabled_generators, ["small_a", "small_b"])
        self.assertEqual(result.cost, 20)
        self.assertFalse(result.shortage)

    def test_exact_generation_match(self) -> None:
        consumers = [Consumer(name="consumer_1", demand=[10] * 24)]
        generators = [Generator(name="diesel_1", kind="diesel", generation=[10] * 24, cost_per_unit=5)]

        result = solve_hour(consumers, generators, 0)

        self.assertEqual(result.total_generation, 10)
        self.assertEqual(result.served_demand, 10)
        self.assertEqual(result.excess_energy, 0)
        self.assertEqual(result.disabled_consumers, [])
        self.assertFalse(result.shortage)

    def test_shortage_maximizes_number_of_enabled_consumers(self) -> None:
        consumers = [
            Consumer(name="consumer_1", demand=[6] * 24),
            Consumer(name="consumer_2", demand=[4] * 24),
            Consumer(name="consumer_3", demand=[4] * 24),
            Consumer(name="consumer_4", demand=[4] * 24),
        ]
        generators = [Generator(name="diesel_1", kind="diesel", generation=[10] * 24, cost_per_unit=5)]

        result = solve_hour(consumers, generators, 0)

        self.assertTrue(result.shortage)
        self.assertEqual(len(result.enabled_consumers), 2)
        self.assertEqual(result.enabled_consumers, ["consumer_1", "consumer_2"])
        self.assertEqual(result.served_demand, 10)

    def test_zero_generation_generator_is_not_selected_without_need(self) -> None:
        consumers = [Consumer(name="consumer_1", demand=[10] * 24)]
        generators = [
            Generator(name="diesel_1", kind="diesel", generation=[10] * 24, cost_per_unit=5),
            Generator(name="solar_1", kind="solar", generation=[0] * 24, cost_per_unit=1),
        ]

        result = solve_hour(consumers, generators, 0)

        self.assertEqual(result.enabled_generators, ["diesel_1"])
        self.assertFalse(result.shortage)

    def test_build_schedule_returns_24_hours(self) -> None:
        consumers = [Consumer(name="consumer_1", demand=[1] * 24)]
        generators = [Generator(name="diesel_1", kind="diesel", generation=[1] * 24, cost_per_unit=5)]

        schedule = build_schedule(consumers, generators)

        self.assertEqual(len(schedule), 24)
        self.assertEqual([item.hour for item in schedule], list(range(24)))
