"""Tests for input validation."""

import json
import tempfile
import unittest
from pathlib import Path

from energy_grid.models import Consumer, Generator
from energy_grid.parser import load_input


class TestValidation(unittest.TestCase):
    def _valid_payload(self) -> dict:
        return {
            "consumers": [
                {
                    "name": "house_1",
                    "demand": [1] * 24,
                }
            ],
            "generators": [
                {
                    "name": "diesel_1",
                    "kind": "diesel",
                    "generation": [2] * 24,
                    "cost_per_unit": 8,
                }
            ],
        }

    def _write_payload(self, payload: dict) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "input.json"
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file)
        return path

    def test_load_valid_input(self) -> None:
        path = self._write_payload(self._valid_payload())

        consumers, generators = load_input(path)

        self.assertEqual(len(consumers), 1)
        self.assertEqual(len(generators), 1)
        self.assertIsInstance(consumers[0], Consumer)
        self.assertIsInstance(generators[0], Generator)
        self.assertEqual(consumers[0].name, "house_1")
        self.assertEqual(generators[0].name, "diesel_1")

    def test_rejects_missing_consumers(self) -> None:
        payload = self._valid_payload()
        del payload["consumers"]
        path = self._write_payload(payload)

        with self.assertRaises(ValueError):
            load_input(path)

        path = self._write_payload({"consumers": [], "generators": payload["generators"]})

        with self.assertRaises(ValueError):
            load_input(path)

    def test_rejects_missing_generators(self) -> None:
        payload = self._valid_payload()
        del payload["generators"]
        path = self._write_payload(payload)

        with self.assertRaises(ValueError):
            load_input(path)

        path = self._write_payload({"consumers": payload["consumers"], "generators": []})

        with self.assertRaises(ValueError):
            load_input(path)

    def test_rejects_wrong_demand_length(self) -> None:
        payload = self._valid_payload()
        payload["consumers"][0]["demand"] = [1] * 23
        path = self._write_payload(payload)

        with self.assertRaises(ValueError):
            load_input(path)

    def test_rejects_wrong_generation_length(self) -> None:
        payload = self._valid_payload()
        payload["generators"][0]["generation"] = [2] * 23
        path = self._write_payload(payload)

        with self.assertRaises(ValueError):
            load_input(path)

    def test_rejects_negative_demand(self) -> None:
        payload = self._valid_payload()
        payload["consumers"][0]["demand"][5] = -1
        path = self._write_payload(payload)

        with self.assertRaises(ValueError):
            load_input(path)

    def test_rejects_negative_generation(self) -> None:
        payload = self._valid_payload()
        payload["generators"][0]["generation"][5] = -1
        path = self._write_payload(payload)

        with self.assertRaises(ValueError):
            load_input(path)

    def test_rejects_negative_cost(self) -> None:
        payload = self._valid_payload()
        payload["generators"][0]["cost_per_unit"] = -0.5
        path = self._write_payload(payload)

        with self.assertRaises(ValueError):
            load_input(path)

    def test_rejects_duplicate_consumer_names(self) -> None:
        payload = self._valid_payload()
        payload["consumers"].append(
            {
                "name": "house_1",
                "demand": [2] * 24,
            }
        )
        path = self._write_payload(payload)

        with self.assertRaises(ValueError):
            load_input(path)

    def test_rejects_duplicate_generator_names(self) -> None:
        payload = self._valid_payload()
        payload["generators"].append(
            {
                "name": "diesel_1",
                "kind": "solar",
                "generation": [3] * 24,
                "cost_per_unit": 1,
            }
        )
        path = self._write_payload(payload)

        with self.assertRaises(ValueError):
            load_input(path)
